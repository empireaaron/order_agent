"""
实时聊天会话模型
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index, Boolean
from sqlalchemy.orm import relationship
from db.session import Base
from utils.timezone import now
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="客户ID")
    agent_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="接入客服ID")
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=True, comment="关联工单ID")

    # 会话状态: waiting(排队中), connected(已接入), closed(已关闭)
    status = Column(String(20), default="waiting", comment="会话状态")

    # 客户请求类型
    request_type = Column(String(50), nullable=True, comment="客户请求类型: order/payment/technical/other")
    initial_message = Column(Text, nullable=True, comment="客户初始消息")

    # 时间戳 - 使用带时区的DateTime
    created_at = Column(DateTime(timezone=True), default=now)
    connected_at = Column(DateTime(timezone=True), nullable=True, comment="客服接入时间")
    closed_at = Column(DateTime(timezone=True), nullable=True, comment="会话关闭时间")
    last_message_at = Column(DateTime(timezone=True), nullable=True, comment="最后消息时间")

    # 关联
    customer = relationship("User", foreign_keys=[customer_id], back_populates="customer_sessions")
    agent = relationship("User", foreign_keys=[agent_id], back_populates="agent_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('ix_chat_sessions_status', 'status'),
        Index('ix_chat_sessions_agent_id', 'agent_id'),
        Index('ix_chat_sessions_customer_id', 'customer_id'),
        Index('ix_chat_sessions_created_at', 'created_at'),
    )


class ChatMessage(Base):
    """聊天记录表"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=True, comment="会话ID，AI聊天时为空")
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="发送者ID: AI/系统消息为NULL")
    sender_type = Column(String(20), nullable=False, comment="发送者类型: customer/agent/system/ai")
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", comment="消息类型: text/image/file/system")

    # 客户ID - 用于简化历史消息查询
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="客户ID: 标识该消息所属的客户")

    # 是否已读
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now)

    # 关联
    session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    customer = relationship("User", foreign_keys=[customer_id])

    # 索引
    __table_args__ = (
        Index('ix_chat_messages_session_id', 'session_id'),
        Index('ix_chat_messages_created_at', 'created_at'),
        Index('ix_chat_messages_sender_id', 'sender_id'),
        Index('ix_chat_messages_customer_id', 'customer_id'),
        Index('ix_chat_messages_sender_type', 'sender_type'),
        Index('ix_chat_messages_customer_session_created', 'customer_id', 'session_id', 'created_at'),
    )


class AgentStatus(Base):
    """客服在线状态表"""
    __tablename__ = "agent_status"

    agent_id = Column(String(36), ForeignKey("users.id"), primary_key=True)

    # 在线状态: online(在线), busy(忙碌), offline(离线)
    status = Column(String(20), default="offline", comment="在线状态")

    # 当前会话数
    current_sessions = Column(Integer, default=0, comment="当前会话数")
    max_sessions = Column(Integer, default=5, comment="最大并发会话数")

    # 今日统计
    total_sessions_today = Column(Integer, default=0)
    total_messages_today = Column(Integer, default=0)

    last_heartbeat = Column(DateTime(timezone=True), default=now, comment="最后心跳时间")
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now)

    # 关联
    agent = relationship("User")