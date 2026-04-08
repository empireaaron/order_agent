"""
用户和角色模型
"""
from uuid import uuid4

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship

from db.session import Base
from utils.timezone import now


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, comment="角色名称")
    code = Column(String(50), unique=True, index=True, comment="角色代码")
    description = Column(String(255), nullable=True, comment="角色描述")
    permissions = Column(JSON, default=list, comment="权限列表")

    # 关系
    users = relationship("User", back_populates="role")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "permissions": self.permissions
        }


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
    username = Column(String(100), unique=True, index=True, comment="用户名")
    email = Column(String(100), unique=True, index=True, comment="邮箱")
    password_hash = Column(String(255), comment="密码哈希")
    full_name = Column(String(100), nullable=True, comment="全名")
    phone = Column(String(20), nullable=True, comment="电话")
    role_id = Column(Integer, ForeignKey("roles.id"), default=1, comment="角色ID")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否验证邮箱")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    created_at = Column(DateTime, default=now, comment="创建时间")
    updated_at = Column(DateTime, default=now, onupdate=now, comment="更新时间")

    # 关系
    role = relationship("Role", back_populates="users")
    tickets = relationship("Ticket", back_populates="customer", foreign_keys="Ticket.customer_id")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_agent_id")
    created_knowledge_bases = relationship("KnowledgeBase", back_populates="owner")
    customer_sessions = relationship("ChatSession", back_populates="customer", foreign_keys="ChatSession.customer_id")
    agent_sessions = relationship("ChatSession", back_populates="agent", foreign_keys="ChatSession.agent_id")

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role_id": self.role_id,
            "role": self.role.to_dict() if self.role else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data

    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        # 管理员拥有所有权限
        if self.role and self.role.code == "admin":
            return True
        # 检查角色权限
        if self.role and permission_code in self.role.permissions:
            return True
        return False


class Ticket(Base):
    """工单模型"""
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
    ticket_no = Column(String(50), unique=True, index=True, comment="工单编号")
    title = Column(String(255), nullable=False, comment="工单标题")
    content = Column(Text, nullable=False, comment="工单内容")
    priority = Column(String(20), default="normal", comment="优先级: low, normal, high, urgent")
    category = Column(String(50), default="general", comment="分类: technical, billing, account, other")
    status = Column(String(30), default="open", comment="状态: open, pending, in_progress, resolved, closed")

    # 关联字段
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="客户ID")
    assigned_agent_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="分配的客服ID")

    # 客户信息快照
    customer_info = Column(JSON, nullable=True, comment="客户信息 (JSON: name, email, phone)")

    # 元数据
    meta_data = Column(JSON, nullable=True, comment="元数据 (JSON)")

    # 时间字段
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")
    closed_at = Column(DateTime, nullable=True, comment="关闭时间")

    created_at = Column(DateTime, default=now, comment="创建时间")
    updated_at = Column(DateTime, default=now, onupdate=now, comment="更新时间")

    # 关系
    customer = relationship("User", back_populates="tickets", foreign_keys=[customer_id])
    assigned_agent = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_agent_id])
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    status_logs = relationship("TicketStatusLog", back_populates="ticket", cascade="all, delete-orphan")

    def to_dict(self, include_full_content=False):
        data = {
            "id": self.id,
            "ticket_no": self.ticket_no,
            "title": self.title,
            "content": self.content if include_full_content else self.content[:200],
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "customer_id": self.customer_id,
            "customer_info": self.customer_info,
            "assigned_agent_id": self.assigned_agent_id,
            "assigned_agent": self.assigned_agent.to_dict() if self.assigned_agent else None,
            "metadata": self.meta_data,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return data


class TicketMessage(Base):
    """工单消息模型"""
    __tablename__ = "ticket_messages"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, comment="工单ID")
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=True, comment="发送者ID (用户ID或NULL表示系统)")
    sender_type = Column(String(20), default="customer", comment="发送者类型: customer, agent, system")
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(20), default="text", comment="消息类型: text, image, file")
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")

    created_at = Column(DateTime, default=now, comment="创建时间")

    # 关系
    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "sender_id": self.sender_id,
            "sender_type": self.sender_type,
            "content": self.content,
            "message_type": self.message_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TicketStatusLog(Base):
    """工单状态变更记录模型"""
    __tablename__ = "ticket_status_logs"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, comment="工单ID")
    from_status = Column(String(30), nullable=True, comment="原状态")
    to_status = Column(String(30), nullable=False, comment="新状态")
    changed_by_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="变更者ID")
    note = Column(Text, nullable=True, comment="备注")

    created_at = Column(DateTime, default=now, comment="创建时间")

    # 关系
    ticket = relationship("Ticket", back_populates="status_logs")
    changed_by = relationship("User", foreign_keys=[changed_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "changed_by_id": self.changed_by_id,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }