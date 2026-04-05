"""
知识库 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel


class KnowledgeBaseBase(BaseModel):
    """知识库基础模型"""
    name: str
    description: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """创建知识库请求"""
    pass


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # active, inactive, building


class KnowledgeBase(KnowledgeBaseBase):
    """知识库响应模型"""
    id: str
    owner_id: str
    collection_name: str
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    document_count: int = 0
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str
    original_filename: str
    file_type: str
    file_size: int = 0


class DocumentCreate(DocumentBase):
    """创建文档请求"""
    pass


class Document(DocumentBase):
    """文档响应模型"""
    id: str
    knowledge_base_id: str
    file_path: Optional[str] = None
    chunk_count: int = 0
    status: str = "processing"
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """检索请求"""
    query: str
    collection_name: str
    top_k: int = 5


class SearchResponse(BaseModel):
    """检索响应"""
    results: List[Dict]
    context: str