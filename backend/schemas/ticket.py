"""
工单 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel, Field, ConfigDict


class TicketBase(BaseModel):
    """工单基础模型"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    priority: str = "normal"
    category: str = "general"
    status: str = "open"


class TicketCreate(TicketBase):
    """创建工单请求"""
    customer_info: Optional[Dict] = None


class TicketUpdate(BaseModel):
    """更新工单请求"""
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    meta_data: Optional[Dict] = None


class TicketMessageBase(BaseModel):
    """工单消息基础模型"""
    content: str = Field(..., min_length=1, max_length=3000)
    message_type: str = "text"


class TicketMessageCreate(TicketMessageBase):
    """创建消息请求"""
    sender_type: str = "customer"


class TicketStatusUpdate(BaseModel):
    """工单状态更新请求"""
    to_status: str = Field(..., min_length=1, max_length=30)
    note: Optional[str] = Field(default=None, max_length=1000)


class TicketMessage(TicketMessageBase):
    """工单消息响应模型"""
    id: str
    ticket_id: str
    sender_id: str
    sender_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketStatusLogBase(BaseModel):
    """状态变更记录基础模型"""
    from_status: Optional[str] = None
    to_status: str
    note: Optional[str] = None


class Ticket(TicketBase):
    """工单响应模型"""
    id: str
    ticket_no: str
    customer_id: str
    assigned_agent_id: Optional[str] = None
    customer_info: Optional[Dict] = None
    meta_data: Optional[Dict] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketList(BaseModel):
    """工单列表响应"""
    total: int
    items: List[Ticket]


class TicketDetail(Ticket):
    """工单详情响应"""
    messages: List[TicketMessageBase] = []
    status_logs: List[TicketStatusLogBase] = []