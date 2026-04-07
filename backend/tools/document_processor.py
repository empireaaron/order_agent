"""
文档处理工具 - 提取内容、分块、向量化、存入 Milvus
"""
import os
import io
from typing import List, Dict
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from db.milvus import milvus_manager
from tools.minio_tools import download_file, get_presigned_url
from config import settings


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    从文件中提取文本内容（使用 LangChain 加载器）

    Args:
        file_path: MinIO object_name
        file_type: 文件类型 (.txt, .pdf, .docx, .md, .html, .csv)

    Returns:
        提取的文本内容
    """
    import tempfile
    import os

    from langchain_community.document_loaders import (
        TextLoader,
        UnstructuredMarkdownLoader,
        Docx2txtLoader,
        CSVLoader
    )

    # 从 MinIO 下载文件内容
    content = download_file(file_path)
    if not content:
        raise ValueError(f"Failed to download file: {file_path}")

    file_type = file_type.lower()

    # 创建临时文件
    suffix_map = {
        ".txt": ".txt",
        ".md": ".md",
        ".pdf": ".pdf",
        ".docx": ".docx",
        ".html": ".html",
        ".csv": ".csv"
    }

    suffix = suffix_map.get(file_type, ".tmp")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        documents = []

        if file_type == ".txt":
            loader = TextLoader(tmp_path, encoding="utf-8")
            documents = loader.load()

        elif file_type == ".md":
            # Markdown 可以直接用 TextLoader 或 UnstructuredMarkdownLoader
            try:
                loader = UnstructuredMarkdownLoader(tmp_path)
                documents = loader.load()
            except Exception:
                # 如果 UnstructuredMarkdownLoader 失败，用 TextLoader
                loader = TextLoader(tmp_path, encoding="utf-8")
                documents = loader.load()

        elif file_type == ".pdf":
            # 使用 pdfplumber 替代 PyPDFLoader，更好地保留阅读顺序
            import pdfplumber
            text = ""
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            return text

        elif file_type == ".docx":
            loader = Docx2txtLoader(tmp_path)
            documents = loader.load()

        elif file_type == ".csv":
            loader = CSVLoader(tmp_path)
            documents = loader.load()

        elif file_type == ".html":
            # HTML 直接读取并简单处理
            html_content = content.decode("utf-8", errors="ignore")
            from html.parser import HTMLParser
            class MLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.fed = []
                def handle_data(self, d):
                    self.fed.append(d)
                def get_data(self):
                    return ''.join(self.fed)

            s = MLStripper()
            s.feed(html_content)
            return s.get_data()

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # 合并所有文档内容
        text = "\n\n".join([doc.page_content for doc in documents])
        return text

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    将文本分割成块

    Args:
        text: 原始文本
        chunk_size: 每块大小
        chunk_overlap: 重叠大小

    Returns:
        文本块列表
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "，", " ", ""]
    )

    chunks = splitter.split_text(text)
    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    生成文本的向量嵌入

    Args:
        texts: 文本列表

    Returns:
        向量列表
    """
    # 检测是否为 DashScope/阿里云
    is_dashscope = "dashscope" in (settings.OPENAI_BASE_URL or "")

    if is_dashscope:
        # DashScope 使用 LangChain 封装
        from langchain_community.embeddings import DashScopeEmbeddings
        embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=settings.OPENAI_API_KEY
        )
    else:
        # OpenAI 官方
        embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
            model="text-embedding-3-small"
        )

    vectors = embeddings.embed_documents(texts)
    return vectors


def process_document(doc_id: str, file_path: str, file_type: str, collection_name: str) -> Dict:
    """
    处理单个文档：提取 -> 分块 -> 向量化 -> 存入 Milvus

    Args:
        doc_id: 文档ID
        file_path: MinIO 中的 object_name
        file_type: 文件类型
        collection_name: Milvus collection 名称

    Returns:
        处理结果 {"success": bool, "chunk_count": int, "error": str}
    """
    try:
        # 1. 提取文本
        print(f"[Process] Extracting text from {file_path}")
        text = extract_text_from_file(file_path, file_type)
        print(f"[Process] Extracted {text} characters")
        if not text or len(text.strip()) == 0:
            return {"success": False, "chunk_count": 0, "error": "No text content extracted"}

        # 2. 分块
        print(f"[Process] Splitting text into chunks")
        chunks = split_text_into_chunks(
            text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        if not chunks:
            return {"success": False, "chunk_count": 0, "error": "No chunks generated"}

        print(f"[Process] Generated {len(chunks)} chunks")

        # 3. 生成向量
        print(f"[Process] Generating embeddings")
        vectors = generate_embeddings(chunks)

        # 4. 准备数据
        data = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            data.append({
                "id": f"{doc_id}_{i}",
                "vector": vector,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "content": chunk  # 存储完整内容
                }
            })

        # 5. 存入 Milvus
        print(f"[Process] Inserting into Milvus collection: {collection_name}")
        success = milvus_manager.insert(collection_name=collection_name, data=data)

        if success:
            return {"success": True, "chunk_count": len(chunks), "error": None}
        else:
            return {"success": False, "chunk_count": 0, "error": "Failed to insert into Milvus"}

    except Exception as e:
        print(f"[Process] Error processing document: {str(e)}")
        return {"success": False, "chunk_count": 0, "error": str(e)}