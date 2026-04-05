"""
知识库模型
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship

from db.session import Base


class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="知识库描述")
    collection_name = Column(String(100), nullable=False, comment="Milvus Collection 名称")
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="所有者ID")
    document_count = Column(Integer, default=0, comment="文档数量")
    status = Column(String(20), default="active", comment="状态: active, inactive, building")
    embedding_model = Column(String(100), default="sentence-transformers/all-MiniLM-L6-v2", comment="嵌入模型")
    meta_data = Column(JSON, nullable=True, comment="元数据")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    owner = relationship("User", back_populates="created_knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "collection_name": self.collection_name,
            "owner_id": self.owner_id,
            "document_count": self.document_count,
            "status": self.status,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id"), nullable=False, comment="知识库ID")
    title = Column(String(255), nullable=False, comment="文档标题")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=True, comment="文件存储路径")
    file_type = Column(String(50), nullable=False, comment="文件类型: txt, pdf, docx, md, html")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    status = Column(String(20), default="processing", comment="状态: processing, indexed, failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    meta_data = Column(JSON, nullable=True, comment="元数据")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    def to_dict(self):
        return {
            "id": self.id,
            "knowledge_base_id": self.knowledge_base_id,
            "title": self.title,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }