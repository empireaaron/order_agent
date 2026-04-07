"""
知识库 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from db.session import get_db
from auth.middleware import get_current_active_user
from models import User, KnowledgeBase, Document
from schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBase as KnowledgeBaseSchema, Document as DocumentSchema, SearchRequest, SearchResponse
from tools.mysql_tools import create_knowledge_base, get_knowledge_bases_by_owner, create_document, update_document_status
from tools.milvus_tools import create_knowledge_base_collection
from tools.minio_tools import upload_file
from tools.document_processor import process_document

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/", response_model=KnowledgeBaseSchema)
def create_knowledge_base_endpoint(
    kb: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建知识库"""
    # 创建 Milvus collection，获取自动生成的 collection_name
    success, collection_name = create_knowledge_base_collection(kb.name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create Milvus collection")

    db_kb = create_knowledge_base(
        db=db,
        name=kb.name,
        description=kb.description,
        collection_name=collection_name,
        owner_id=current_user.id
    )
    return db_kb


@router.get("/", response_model=list[KnowledgeBaseSchema])
def read_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的所有知识库"""
    kbs = get_knowledge_bases_by_owner(db=db, owner_id=current_user.id)
    return kbs


@router.get("/{kb_id}", response_model=KnowledgeBaseSchema)
def read_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取知识库详情"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseSchema)
def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 检查权限
    if kb.owner_id != current_user.id and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not allowed to update this knowledge base")

    # 更新字段
    if kb_update.name is not None:
        kb.name = kb_update.name
    if kb_update.description is not None:
        kb.description = kb_update.description
    if kb_update.status is not None:
        kb.status = kb_update.status

    db.commit()
    db.refresh(kb)
    return kb


@router.post("/{kb_id}/documents")
def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传文档到知识库"""
    # 验证知识库所有权
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    if kb.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to add documents to this knowledge base")

    # 限制文件类型
    allowed_types = [".txt", ".pdf", ".docx", ".doc", ".md", ".html"]
    file_ext = "." + file.filename.split(".")[-1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {allowed_types}")

    # 读取文件内容并上传到 MinIO
    try:
        content = file.file.read()
        object_name = f"{kb_id}/{file.filename}"

        # 上传到 MinIO
        success, result = upload_file(
            file_data=content,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream"
        )

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {result}")

        # 创建文档记录
        db_doc = create_document(
            db=db,
            knowledge_base_id=kb_id,
            title=file.filename,
            original_filename=file.filename,
            file_type=file_ext,
            file_size=len(content)
        )

        # 更新文件路径为 MinIO URL
        db_doc.file_path = object_name  # 存储 object_name 而不是 URL
        db_doc.status = "processing"  # 标记为处理中
        db.commit()
        db.refresh(db_doc)

        # 保存需要用到的变量副本
        doc_id = str(db_doc.id)
        collection_name = str(kb.collection_name)

        # 异步处理文档（向量化）
        import threading
        def process_in_background(doc_id_copy, object_name_copy, file_ext_copy, collection_name_copy):
            # 在线程内创建新的 session
            from db.session import SessionLocal
            thread_db = SessionLocal()
            try:
                result = process_document(
                    doc_id=doc_id_copy,
                    file_path=object_name_copy,
                    file_type=file_ext_copy,
                    collection_name=collection_name_copy
                )
                if result["success"]:
                    update_document_status(
                        db=thread_db,
                        doc_id=doc_id_copy,
                        status="indexed",
                        chunk_count=result["chunk_count"]
                    )
                else:
                    update_document_status(
                        db=thread_db,
                        doc_id=doc_id_copy,
                        status="failed",
                        error_message=result["error"]
                    )
            except Exception as e:
                update_document_status(
                    db=thread_db,
                    doc_id=doc_id_copy,
                    status="failed",
                    error_message=str(e)
                )
            finally:
                thread_db.close()

        # 启动后台线程处理
        thread = threading.Thread(
            target=process_in_background,
            args=(doc_id, object_name, file_ext, collection_name)
        )
        thread.start()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    # 返回上传信息
    return {
        "id": db_doc.id,
        "filename": file.filename,
        "status": "processing",
        "message": "File uploaded and processing in background"
    }


@router.get("/{kb_id}/documents", response_model=list[DocumentSchema])
def read_documents(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取知识库的文档列表"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    documents = db.query(Document).filter(Document.knowledge_base_id == kb_id).all()
    return documents


@router.delete("/{kb_id}/documents/{doc_id}")
def delete_document(
    kb_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除知识库中的文档"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.knowledge_base_id == kb_id
    ).first()

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. 从 MinIO 删除文件
    try:
        from tools.minio_tools import delete_file
        delete_file(doc.file_path)
    except Exception as e:
        print(f"Warning: Failed to delete file from MinIO: {e}")

    # 2. 从 Milvus 删除该文档的所有向量数据
    try:
        from db.milvus import milvus_manager
        milvus_manager.delete(
            collection_name=kb.collection_name,
            expr=f"id like '{doc.id}_%'"
        )
    except Exception as e:
        print(f"Warning: Failed to delete vectors from Milvus: {e}")

    # 3. 删除数据库记录
    db.delete(doc)
    db.commit()

    # 4. 更新知识库文档计数
    kb.document_count = db.query(Document).filter(
        Document.knowledge_base_id == kb_id
    ).count()
    db.commit()

    return {"message": "Document deleted successfully"}


@router.delete("/{kb_id}")
def delete_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 检查权限（只有所有者或管理员可以删除）
    if kb.owner_id != current_user.id and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Not allowed to delete this knowledge base")

    # 删除 Milvus collection
    try:
        from db.milvus import milvus_manager
        milvus_manager.drop_collection(kb.collection_name)
    except Exception as e:
        print(f"Warning: Failed to drop Milvus collection: {e}")

    # 删除相关文档记录
    db.query(Document).filter(Document.knowledge_base_id == kb_id).delete()

    # 删除知识库
    db.delete(kb)
    db.commit()

    return {"message": "Knowledge base deleted successfully"}


@router.post("/search")
def search_knowledge_base(
    search: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """在知识库中搜索"""
    from tools.milvus_tools import search_kb
    context = search_kb(
        question=search.query,
        collection_name=search.collection_name,
        top_k=search.top_k
    )
    return SearchResponse(results=[], context=context)