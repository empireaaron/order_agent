"""
Mysql 工具函数 - 工单 CRUD
"""
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from models import Ticket, TicketMessage, TicketStatusLog, KnowledgeBase, Document


# 工单操作
def create_ticket(
    db: Session,
    title: str,
    content: str,
    customer_id: str,
    priority: str = "normal",
    category: str = "general",
    customer_info: Dict = None
) -> Ticket:
    """创建工单"""
    # 生成工单编号
    ticket_no = f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    ticket = Ticket(
        id=str(uuid4()),
        ticket_no=ticket_no,
        title=title,
        content=content,
        priority=priority,
        category=category,
        customer_id=customer_id,
        customer_info=customer_info
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


def get_ticket_by_id(db: Session, ticket_id: str) -> Optional[Ticket]:
    """根据 ID 获取工单"""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets_by_customer(
    db: Session,
    customer_id: str,
    skip: int = 0,
    limit: int = 10
) -> List[Ticket]:
    """获取客户的所有工单"""
    return db.query(Ticket)\
        .filter(Ticket.customer_id == customer_id)\
        .order_by(Ticket.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_all_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 10
) -> List[Ticket]:
    """获取所有工单（管理员）"""
    return db.query(Ticket)\
        .order_by(Ticket.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def update_ticket_status(
    db: Session,
    ticket_id: str,
    to_status: str,
    changed_by_id: str,
    note: str = None
) -> Optional[Ticket]:
    """更新工单状态"""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        return None

    from_status = ticket.status
    ticket.status = to_status
    ticket.updated_at = datetime.utcnow()

    # 记录状态变更
    status_log = TicketStatusLog(
        id=str(uuid4()),
        ticket_id=ticket_id,
        from_status=from_status,
        to_status=to_status,
        changed_by_id=changed_by_id,
        note=note
    )
    db.add(status_log)

    db.commit()
    db.refresh(ticket)
    return ticket


# 消息操作
def add_ticket_message(
    db: Session,
    ticket_id: str,
    sender_id: str,
    sender_type: str,
    content: str
) -> TicketMessage:
    """添加工单消息"""
    message = TicketMessage(
        id=str(uuid4()),
        ticket_id=ticket_id,
        sender_id=sender_id,
        sender_type=sender_type,
        content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_ticket_messages(
    db: Session,
    ticket_id: str
) -> list[TicketMessage]:
    """获取工单的所有消息"""
    from models import TicketMessage as TicketMessageModel
    messages = db.query(TicketMessageModel).filter(
        TicketMessageModel.ticket_id == ticket_id
    ).order_by(TicketMessageModel.created_at.asc()).all()
    return messages


# 知识库操作
def create_knowledge_base(
    db: Session,
    name: str,
    description: str,
    collection_name: str,
    owner_id: str
) -> KnowledgeBase:
    """创建知识库"""
    kb = KnowledgeBase(
        id=str(uuid4()),
        name=name,
        description=description,
        collection_name=collection_name,
        owner_id=owner_id
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


def get_knowledge_bases_by_owner(
    db: Session,
    owner_id: str
) -> List[KnowledgeBase]:
    """获取所有者的所有知识库"""
    return db.query(KnowledgeBase)\
        .filter(KnowledgeBase.owner_id == owner_id)\
        .all()


# 文档操作
def create_document(
    db: Session,
    knowledge_base_id: str,
    title: str,
    original_filename: str,
    file_type: str,
    file_size: int = 0
) -> Document:
    """创建文档记录"""
    doc = Document(
        id=str(uuid4()),
        knowledge_base_id=knowledge_base_id,
        title=title,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document_status(
    db: Session,
    doc_id: str,
    status: str,
    chunk_count: int = 0,
    error_message: str = None
) -> Optional[Document]:
    """更新文档状态"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return None

    doc.status = status
    doc.chunk_count = chunk_count
    doc.error_message = error_message
    db.commit()
    db.refresh(doc)
    return doc