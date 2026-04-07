"""
MySQL 数据库会话管理
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

try:
    from config import settings
except ImportError:
    # 如果直接运行此文件，使用相对导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import settings

# 创建 SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话（用于 FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Session:
    """获取数据库会话上下文管理器（用于非路由代码）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    # 导入所有模型
    from models import User, Role, Ticket, TicketMessage, TicketStatusLog, KnowledgeBase, Document

    Base.metadata.create_all(bind=engine)


def drop_db():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)