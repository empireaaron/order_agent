"""
实时客服聊天 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import timedelta
import asyncio

from db.session import get_db
from auth.middleware import get_current_active_user
from models import User
from models.chat import ChatSession, ChatMessage, AgentStatus
from websocket.chat import chat_ws_manager
from utils.timezone import now

router = APIRouter(prefix="/chat-service", tags=["Chat Service"])


async def notify_session_assigned(user_id: str, session_id: str, agent_id: str, agent_name: str):
    """后台任务：通知客户被接入"""
    await chat_ws_manager.send_to_user(
        user_id,
        {
            "type": "session_assigned",
            "session_id": session_id,
            "agent": {
                "id": agent_id,
                "name": agent_name
            }
        }
    )


async def notify_system_message(session_id: str, msg_id: str, content: str):
    """后台任务：广播系统消息"""
    await chat_ws_manager.send_to_session(
        session_id,
        {
            "type": "new_message",
            "session_id": session_id,
            "message": {
                "id": msg_id,
                "content": content,
                "sender_type": "system",
                "created_at": now().isoformat()
            }
        }
    )


async def notify_new_waiting_session(session_id: str, customer_id: str, customer_name: str, initial_message: str):
    """后台任务：通知客服有新会话"""
    await chat_ws_manager.broadcast_to_agents({
        "type": "new_waiting_session",
        "session_id": session_id,
        "customer": {
            "id": customer_id,
            "username": customer_name
        },
        "initial_message": initial_message,
        "created_at": now().isoformat()
    })


async def notify_chat_message(session_id: str, msg_id: str, content: str, sender_type: str, sender_id: str, sender_name: str):
    """后台任务：广播聊天消息"""
    await chat_ws_manager.send_to_session(
        session_id,
        {
            "type": "new_message",
            "session_id": session_id,
            "message": {
                "id": msg_id,
                "content": content,
                "sender_type": sender_type,
                "sender": {
                    "id": sender_id,
                    "name": sender_name
                },
                "created_at": now().isoformat()
            }
        }
    )


async def notify_agent_new_session(agent_id: str, session_id: str, customer_info: dict):
    """后台任务：通知客服有新会话分配"""
    await chat_ws_manager.send_to_user(
        agent_id,
        {
            "type": "session_assigned",
            "session_id": session_id,
            "customer": customer_info
        }
    )


async def notify_session_closed(session_id: str, customer_id: str, agent_id: str | None, closed_by: str):
    """后台任务：通知双方会话已关闭"""
    message = {
        "type": "session_closed",
        "session_id": session_id,
        "closed_by": closed_by,
        "message": f"会话已被 {closed_by} 关闭"
    }
    # 通知客户
    await chat_ws_manager.send_to_user(customer_id, message)
    # 通知客服（如果有）
    if agent_id:
        await chat_ws_manager.send_to_user(agent_id, message)


@router.post("/sessions")
def create_chat_session(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    客户发起转人工，创建聊天会话
    """
    try:
        print(f"DEBUG: Creating chat session for user {current_user.id}")
        print(f"DEBUG: Request body: {request}")

        # 检查是否已有进行中的会话
        existing = db.query(ChatSession).filter(
            ChatSession.customer_id == current_user.id,
            ChatSession.status.in_(["waiting", "connected"])
        ).first()

        print(f"DEBUG: Existing session check: {existing}")

        if existing:
            print(f"DEBUG: Found existing session {existing.id}, status={existing.status}")

            # 如果已有 connected 状态的会话，直接返回
            if existing.status == "connected":
                return {
                    "session_id": existing.id,
                    "status": existing.status,
                    "queue_position": 0,
                    "agent": {
                        "id": existing.agent_id,
                        "name": existing.agent.full_name or existing.agent.username
                    } if existing.agent else None,
                    "message": "您已有进行中的会话"
                }
            # 如果已有 waiting 状态的会话，返回排队位置
            queue_pos = get_queue_position(db, existing.id)
            print(f"DEBUG: Existing session queue position: {queue_pos}")
            return {
                "session_id": existing.id,
                "status": existing.status,
                "queue_position": queue_pos,
                "message": f"您已在排队中，当前位置：第{queue_pos}位"
            }

        # 创建新会话
        print(f"DEBUG: Creating new chat session")
        session = ChatSession(
            customer_id=current_user.id,
            status="waiting",
            request_type=request.get("request_type", "general"),
            initial_message=request.get("message", "")
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"DEBUG: Session created: {session.id}")

        # 尝试自动分配客服
        print(f"DEBUG: Trying to auto-assign agent")
        assigned_agent = auto_assign_agent(db)
        print(f"DEBUG: Auto-assign result: {assigned_agent}")
        if assigned_agent:
            session.agent_id = assigned_agent.agent_id
            session.status = "connected"
            session.connected_at = now()
            db.commit()

            # 发送系统消息
            system_msg = ChatMessage(
                session_id=session.id,
                sender_id=None,  # 系统消息sender_id为NULL
                sender_type="system",
                content=f"客服 {assigned_agent.agent.username} 已接入会话",
                customer_id=session.customer_id  # 设置customer_id方便查询
            )
            db.add(system_msg)
            db.commit()
            db.refresh(system_msg)

            # WebSocket通知客户被接入（后台任务）
            background_tasks.add_task(
                notify_session_assigned,
                current_user.id,
                session.id,
                assigned_agent.agent_id,
                assigned_agent.agent.full_name or assigned_agent.agent.username
            )

            # WebSocket通知客服有新会话分配（后台任务）
            background_tasks.add_task(
                notify_agent_new_session,
                assigned_agent.agent_id,
                session.id,
                {
                    "id": current_user.id,
                    "username": current_user.username
                }
            )

            # 广播系统消息给会话双方（后台任务）
            background_tasks.add_task(
                notify_system_message,
                session.id,
                system_msg.id,
                system_msg.content
            )

            return {
                "session_id": session.id,
                "status": "connected",
                "agent": {
                    "id": assigned_agent.agent_id,
                    "name": assigned_agent.agent.full_name or assigned_agent.agent.username
                },
                "message": f"客服 {assigned_agent.agent.full_name or assigned_agent.agent.username} 为您服务"
            }

        # 进入排队
        queue_pos = get_queue_position(db, session.id)

        # 广播通知所有在线客服有新会话（后台任务）
        background_tasks.add_task(
            notify_new_waiting_session,
            session.id,
            current_user.id,
            current_user.username,
            session.initial_message
        )

        return {
            "session_id": session.id,
            "status": "waiting",
            "queue_position": queue_pos,
            "message": f"正在为您转接人工客服，当前排队位置：第{queue_pos}位"
        }
    except Exception as e:
        import traceback
        print(f"Error creating chat session: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/sessions/waiting")
def get_waiting_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    客服获取等待队列（仅客服/管理员）
    """
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    sessions = db.query(ChatSession).filter(
        ChatSession.status == "waiting"
    ).order_by(ChatSession.created_at).all()

    return [{
        "id": s.id,
        "customer": {
            "id": s.customer_id,
            "username": s.customer.username,
            "email": s.customer.email
        },
        "request_type": s.request_type,
        "initial_message": s.initial_message,
        "created_at": s.created_at.isoformat(),
        "wait_time_seconds": (now() - s.created_at).seconds
    } for s in sessions]


@router.post("/sessions/{session_id}/accept")
def accept_chat_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    客服接入会话
    """
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.status == "waiting"
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or already assigned")

    # 检查客服当前会话数
    agent_status = db.query(AgentStatus).filter(
        AgentStatus.agent_id == current_user.id
    ).first()

    if agent_status and int(agent_status.current_sessions) >= int(agent_status.max_sessions):
        raise HTTPException(status_code=400, detail="您已达到最大并发会话数")

    # 分配会话
    session.agent_id = current_user.id
    session.status = "connected"
    session.connected_at = now()
    db.commit()

    # 更新客服状态
    if agent_status:
        agent_status.current_sessions = str(int(agent_status.current_sessions) + 1)
        agent_status.total_sessions_today = str(int(agent_status.total_sessions_today) + 1)
        db.commit()

    # 发送系统消息
    system_msg = ChatMessage(
        session_id=session.id,
        sender_id=None,  # 系统消息sender_id为NULL
        sender_type="system",
        content=f"客服 {current_user.full_name or current_user.username} 已接入会话",
        customer_id=session.customer_id  # 设置customer_id方便查询
    )
    db.add(system_msg)
    db.commit()
    db.refresh(system_msg)

    # WebSocket通知客户被接入（后台任务）
    background_tasks.add_task(
        notify_session_assigned,
        session.customer_id,
        session.id,
        current_user.id,
        current_user.full_name or current_user.username
    )

    # WebSocket广播系统消息给会话双方（后台任务）
    background_tasks.add_task(
        notify_system_message,
        session.id,
        system_msg.id,
        system_msg.content
    )

    return {
        "session_id": session.id,
        "status": "connected",
        "customer": {
            "id": session.customer_id,
            "username": session.customer.username
        }
    }


@router.get("/sessions/my")
def get_my_chat_sessions(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取我的会话列表（客户或客服）
    """
    query = db.query(ChatSession)

    if current_user.role.code in ["admin", "agent"]:
        # 客服查看分配的会话
        query = query.filter(ChatSession.agent_id == current_user.id)
    else:
        # 客户查看自己的会话
        query = query.filter(ChatSession.customer_id == current_user.id)

    if status:
        query = query.filter(ChatSession.status == status)
    else:
        query = query.filter(ChatSession.status.in_(["waiting", "connected"]))

    sessions = query.order_by(ChatSession.last_message_at.desc()).all()

    return [{
        "id": s.id,
        "status": s.status,
        "customer": {
            "id": s.customer_id,
            "username": s.customer.username
        } if s.customer else None,
        "agent": {
            "id": s.agent_id,
            "name": s.agent.full_name or s.agent.username
        } if s.agent else None,
        "last_message": s.messages[-1].content if s.messages else None,
        "unread_count": len([m for m in s.messages if m.sender_type != (
            "agent" if current_user.role.code in ["admin", "agent"] else "customer"
        ) and m.is_read == "0"]),
        "created_at": s.created_at.isoformat()
    } for s in sessions]


@router.post("/sessions/{session_id}/messages")
def send_chat_message(
    session_id: str,
    message: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    发送聊天消息
    sender_id 规则:
    - 客户消息: sender_id = 客户ID
    - 客服消息: sender_id = 客服ID
    - AI/系统消息: sender_id = NULL
    customer_id 始终设置为该会话的客户ID
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 检查权限
    if current_user.id not in [session.customer_id, session.agent_id]:
        raise HTTPException(status_code=403, detail="Not allowed")

    sender_type = "agent" if current_user.role.code in ["admin", "agent"] else "customer"

    # 创建消息 - 设置 customer_id 为该会话的客户ID
    chat_msg = ChatMessage(
        session_id=session_id,
        sender_id=current_user.id,
        sender_type=sender_type,
        content=message.get("content", ""),
        message_type=message.get("type", "text"),
        customer_id=session.customer_id  # 统一设置customer_id方便查询
    )
    db.add(chat_msg)

    # 更新会话最后消息时间
    session.last_message_at = now()
    db.commit()
    db.refresh(chat_msg)

    # WebSocket广播消息给会话中的所有用户（后台任务）
    background_tasks.add_task(
        notify_chat_message,
        session_id,
        chat_msg.id,
        chat_msg.content,
        sender_type,
        current_user.id,
        current_user.full_name or current_user.username
    )

    return {
        "id": chat_msg.id,
        "content": chat_msg.content,
        "sender_type": chat_msg.sender_type,
        "created_at": chat_msg.created_at.isoformat()
    }


@router.get("/sessions/{session_id}/messages")
def get_chat_messages(
    session_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页消息数，最大100"),
    include_ai_history: bool = Query(True, description="是否包含AI聊天历史"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取会话消息历史（分页加载）
    如果 include_ai_history=True，同时返回该客户与AI的历史聊天记录

    查询优化：使用 customer_id 字段直接查询，无需复杂关联
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.id not in [session.customer_id, session.agent_id]:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 获取客户ID（当前用户可能是客户或客服）
    customer_id = session.customer_id

    if include_ai_history:
        # 简化查询：使用 customer_id 字段直接查询
        # 1. AI聊天阶段：customer_id = 客户ID 且 session_id IS NULL
        # 2. 客服聊天阶段：该客户的所有会话消息

        # 先获取该客户的所有会话ID
        customer_session_ids = db.query(ChatSession.id).filter(
            ChatSession.customer_id == customer_id
        ).all()
        customer_session_ids = [s[0] for s in customer_session_ids]

        # 构建查询 - 简化版：使用 customer_id
        query = db.query(ChatMessage).filter(
            or_(
                # AI聊天阶段：该客户的所有消息（通过customer_id关联）
                and_(
                    ChatMessage.customer_id == customer_id,
                    ChatMessage.session_id.is_(None)
                ),
                # 客服聊天阶段：该客户的所有会话消息
                ChatMessage.session_id.in_(customer_session_ids) if customer_session_ids else False
            )
        )

        total = query.count()
        offset = (page - 1) * page_size
        messages = query.order_by(ChatMessage.created_at.asc()).offset(offset).limit(page_size).all()
    else:
        # 只查询当前会话的消息
        total = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).count()

        offset = (page - 1) * page_size

        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(page_size).all()

    print(f"DEBUG: get_chat_messages: session_id={session_id}, page={page}, total={total}, returned={len(messages)}, include_ai={include_ai_history}")
    for m in messages[:3]:
        print(f"DEBUG:   msg: sender_type={m.sender_type}, session={m.session_id}, sender={m.sender_id}, content={m.content[:30]}...")

    return {
        "items": [{
            "id": m.id,
            "content": m.content,
            "sender_type": m.sender_type,
            "sender": {
                "id": m.sender_id,
                "name": m.sender.full_name or m.sender.username if m.sender else None
            } if m.sender_id else None,
            "is_read": m.is_read == "1",
            "created_at": m.created_at.isoformat()
        } for m in messages],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": offset + len(messages) < total
    }


@router.post("/sessions/{session_id}/close")
def close_chat_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    关闭会话
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.id not in [session.customer_id, session.agent_id]:
        raise HTTPException(status_code=403, detail="Not allowed")

    session.status = "closed"
    session.closed_at = now()
    db.commit()

    # 更新客服会话数
    if session.agent_id:
        agent_status = db.query(AgentStatus).filter(
            AgentStatus.agent_id == session.agent_id
        ).first()
        if agent_status:
            agent_status.current_sessions = str(max(0, int(agent_status.current_sessions) - 1))
            db.commit()

    # WebSocket 通知双方会话已关闭
    background_tasks.add_task(
        notify_session_closed,
        session_id,
        str(session.customer_id),
        str(session.agent_id) if session.agent_id else None,
        current_user.full_name or current_user.username
    )

    return {"message": "Session closed"}


@router.post("/agent/online")
def set_agent_online(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """客服上线"""
    print(f"DEBUG: set_agent_online called, user_id={current_user.id}, role={current_user.role.code}")

    if current_user.role.code not in ["admin", "agent"]:
        print(f"DEBUG: Permission denied for role {current_user.role.code}")
        raise HTTPException(status_code=403, detail="Permission denied")

    agent_status = db.query(AgentStatus).filter(
        AgentStatus.agent_id == current_user.id
    ).first()

    if not agent_status:
        print(f"DEBUG: Creating new agent status for {current_user.id}")
        agent_status = AgentStatus(
            agent_id=current_user.id,
            status="online",
            max_sessions="5"
        )
        db.add(agent_status)
    else:
        print(f"DEBUG: Updating agent status to online for {current_user.id}")
        agent_status.status = "online"

    db.commit()
    print(f"DEBUG: Agent {current_user.id} is now online")
    return {"status": "online"}


@router.post("/agent/offline")
def set_agent_offline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """客服下线"""
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    agent_status = db.query(AgentStatus).filter(
        AgentStatus.agent_id == current_user.id
    ).first()

    if agent_status:
        agent_status.status = "offline"
        db.commit()

    return {"status": "offline"}


# ============ 辅助函数 ============

def get_queue_position(db: Session, session_id: str) -> int:
    """获取排队位置"""
    waiting = db.query(ChatSession).filter(
        ChatSession.status == "waiting"
    ).order_by(ChatSession.created_at).all()

    print(f"DEBUG: get_queue_position called for session {session_id}")
    print(f"DEBUG: Found {len(waiting)} waiting sessions")

    for i, s in enumerate(waiting, 1):
        sid = str(s.id)
        target_sid = str(session_id)
        print(f"DEBUG: Checking position {i}, session {sid} vs target {target_sid}")
        if sid == target_sid:
            print(f"DEBUG: Found match at position {i}")
            return i

    print(f"DEBUG: Session {session_id} not found in waiting list ({len(waiting)} waiting)")
    # 如果会话不在等待列表中，返回最后位置+1
    return len(waiting) + 1


def auto_assign_agent(db: Session) -> Optional[AgentStatus]:
    """自动分配可用客服"""
    # 查找在线且未满的客服
    agents = db.query(AgentStatus).filter(
        AgentStatus.status == "online"
    ).order_by(AgentStatus.current_sessions).all()

    for agent in agents:
        try:
            current = int(agent.current_sessions or 0)
            max_sess = int(agent.max_sessions or 5)
            if current < max_sess:
                print(f"DEBUG: Found available agent {agent.agent_id} with {current}/{max_sess} sessions")
                return agent
        except (ValueError, TypeError):
            continue

    print(f"DEBUG: No available agent found among {len(agents)} online agents")
    return None


@router.post("/ai-messages")
def save_ai_message(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    保存AI聊天消息（转人工前的AI对话记录）
    sender_id 使用规则：
    - 客户消息：sender_id = 客户ID
    - AI消息：sender_id = NULL
    - customer_id = 客户ID（用于简化查询）
    """
    try:
        role = request.get("role")  # 'customer' 或 'ai'
        content = request.get("content")

        print(f"DEBUG: save_ai_message called: role={role}, content={content[:50]}...")

        if not role or not content:
            raise HTTPException(status_code=400, detail="Missing role or content")

        # 保存消息，session_id 为空表示这是AI聊天（未转人工）
        # sender_id 规则：客户消息用客户ID，AI消息用NULL
        msg = ChatMessage(
            session_id=None,
            sender_id=current_user.id if role == "customer" else None,
            sender_type=role,
            content=content,
            message_type="text",
            customer_id=current_user.id  # 统一设置customer_id方便查询
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        print(f"DEBUG: Saved AI message: id={msg.id}, role={role}, sender={msg.sender_id}, customer={msg.customer_id}")

        return {
            "id": msg.id,
            "role": role,
            "content": content,
            "created_at": msg.created_at.isoformat()
        }
    except Exception as e:
        import traceback
        print(f"Error saving AI message: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"保存消息失败: {str(e)}")


@router.get("/ai-messages")
def get_ai_messages(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页消息数，最大100"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的所有AI聊天历史（包括已转人工和未转人工的）
    优化：使用 customer_id 字段直接查询
    """
    try:
        print(f"DEBUG: get_ai_messages for user {current_user.id}, page={page}, page_size={page_size}")

        # 查询优化：使用 customer_id 字段直接查询
        # 筛选条件：customer_id = 当前用户ID 且 session_id IS NULL（AI聊天阶段）
        total = db.query(ChatMessage).filter(
            ChatMessage.customer_id == current_user.id,
            ChatMessage.session_id.is_(None),
            ChatMessage.sender_type.in_(["customer", "ai"])
        ).count()

        # 分页查询
        offset = (page - 1) * page_size
        messages = db.query(ChatMessage).filter(
            ChatMessage.customer_id == current_user.id,
            ChatMessage.session_id.is_(None),
            ChatMessage.sender_type.in_(["customer", "ai"])
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(page_size).all()

        print(f"DEBUG: Found {len(messages)} AI messages (total={total})")

        return {
            "items": [{
                "id": m.id,
                "role": m.sender_type,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "session_id": m.session_id
            } for m in messages],
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(messages) < total
        }
    except Exception as e:
        print(f"Error getting AI messages: {e}")
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")