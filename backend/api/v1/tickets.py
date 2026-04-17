"""
工单 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from auth.middleware import get_current_active_user, ROLE_ADMIN, ROLE_AGENT
from models import User, Ticket as TicketModel
from schemas.ticket import TicketCreate, TicketUpdate, TicketMessageCreate, TicketMessage, Ticket as TicketSchema
from tools.mysql_tools import create_ticket, get_tickets_by_customer, get_ticket_by_id, update_ticket_status, add_ticket_message, get_ticket_messages, get_all_tickets

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/", response_model=TicketSchema)
def create_new_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新工单"""
    db_ticket = create_ticket(
        db=db,
        title=ticket.title,
        content=ticket.content,
        customer_id=current_user.id,
        priority=ticket.priority,
        category=ticket.category,
        customer_info=ticket.customer_info
    )
    return db_ticket


@router.get("/", response_model=list[TicketSchema])
def read_user_tickets(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的所有工单"""
    tickets = get_tickets_by_customer(
        db=db,
        customer_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return tickets


@router.get("/{ticket_id}", response_model=TicketSchema)
def read_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取工单详情"""
    ticket = get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketSchema)
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新工单"""
    ticket = get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # 只有客服或管理员可以更新工单
    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        if ticket.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to update this ticket")

    # 更新字段（根据角色限制可更新字段，禁止反射赋值绕过权限）
    update_data = ticket_update.model_dump(exclude_unset=True)

    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        # 普通客户只允许更新 title 和 content
        allowed_fields = {"title", "content"}
        for key in list(update_data.keys()):
            if key not in allowed_fields:
                raise HTTPException(
                    status_code=403,
                    detail=f"Customers are not allowed to update field: {key}"
                )
    else:
        # 客服/管理员不允许通过此接口修改部分系统字段
        disallowed_fields = {"id", "customer_id", "ticket_no", "created_at", "updated_at", "resolved_at", "closed_at"}
        for key in list(update_data.keys()):
            if key in disallowed_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field cannot be updated: {key}"
                )

    for key, value in update_data.items():
        setattr(ticket, key, value)

    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/messages")
def add_ticket_message_endpoint(
    ticket_id: str,
    message: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """添加工单消息，根据发送者自动更新工单状态"""
    ticket = get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # 添加消息
    db_message = add_ticket_message(
        db=db,
        ticket_id=ticket_id,
        sender_id=current_user.id,
        sender_type=message.sender_type,
        content=message.content
    )

    # 自动状态变更逻辑（已解决和已关闭状态不自动变更）
    if ticket.status not in ["resolved", "closed"]:
        if message.sender_type == "customer":
            # 客户发送消息 -> 变为待回复（提醒客服处理）
            if ticket.status in ["open", "in_progress"]:
                ticket.status = "pending"
                db.commit()
        elif message.sender_type == "agent":
            # 客服发送消息 -> 变为处理中
            if ticket.status in ["open", "pending"]:
                ticket.status = "in_progress"
                db.commit()

    return db_message


@router.get("/{ticket_id}/messages", response_model=list[TicketMessage])
def read_ticket_messages(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取工单的所有消息"""
    ticket = get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    messages = get_ticket_messages(db=db, ticket_id=ticket_id)
    return messages


@router.get("/admin/all", response_model=list[TicketSchema])
def read_all_tickets(
    status: str = None,
    priority: str = None,
    assigned_to_me: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有工单（仅客服/管理员）"""
    # 检查权限
    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        raise HTTPException(status_code=403, detail="Permission denied")

    query = db.query(TicketModel)

    # 筛选状态
    if status:
        query = query.filter(TicketModel.status == status)

    # 筛选优先级
    if priority:
        query = query.filter(TicketModel.priority == priority)

    # 只查看分配给我的
    if assigned_to_me:
        query = query.filter(TicketModel.assigned_agent_id == current_user.id)
    # 未分配的工单
    elif assigned_to_me is False and status == "open":
        query = query.filter(TicketModel.assigned_agent_id.is_(None))

    tickets = query.order_by(TicketModel.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.patch("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分配工单给当前客服"""
    # 检查权限
    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        raise HTTPException(status_code=403, detail="Permission denied")

    ticket = get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # 更新分配
    ticket.assigned_agent_id = current_user.id
    ticket.status = "in_progress"
    db.commit()
    db.refresh(ticket)

    return {"message": "Ticket assigned successfully", "ticket": ticket}


@router.patch("/{ticket_id}/status")
def update_ticket_status_endpoint(
    ticket_id: str,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新工单状态"""
    ticket = get_ticket_by_id(db=db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    to_status = status_update.get("to_status")
    note = status_update.get("note")

    ticket = update_ticket_status(
        db=db,
        ticket_id=ticket_id,
        to_status=to_status,
        changed_by_id=current_user.id,
        note=note
    )
    return ticket