"""
实时客服聊天 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import asyncio

from db.session import get_db
from auth.middleware import get_current_active_user
from models import User
from models.chat import ChatSession, ChatMessage, AgentStatus
from websocket.chat import chat_ws_manager

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
                "created_at": datetime.utcnow().isoformat()
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
        "created_at": datetime.utcnow().isoformat()
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
                "created_at": datetime.utcnow().isoformat()
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

        # 检查是否已有进行中的会话
        existing = db.query(ChatSession).filter(
            ChatSession.customer_id == current_user.id,
            ChatSession.status.in_(["waiting", "connected"])
        ).first()

        print(f"DEBUG: Existing session check: {existing}")

        if existing:
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
            session.connected_at = datetime.utcnow()
            db.commit()

            # 发送系统消息
            system_msg = ChatMessage(
                session_id=session.id,
                sender_id=assigned_agent.agent_id,
                sender_type="system",
                content=f"客服 {assigned_agent.agent.username} 已接入会话"
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
        "wait_time_seconds": (datetime.utcnow() - s.created_at).seconds
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
    session.connected_at = datetime.utcnow()
    db.commit()

    # 更新客服状态
    if agent_status:
        agent_status.current_sessions = str(int(agent_status.current_sessions) + 1)
        agent_status.total_sessions_today = str(int(agent_status.total_sessions_today) + 1)
        db.commit()

    # 发送系统消息
    system_msg = ChatMessage(
        session_id=session.id,
        sender_id=current_user.id,
        sender_type="system",
        content=f"客服 {current_user.full_name or current_user.username} 已接入会话"
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
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 检查权限
    if current_user.id not in [session.customer_id, session.agent_id]:
        raise HTTPException(status_code=403, detail="Not allowed")

    sender_type = "agent" if current_user.role.code in ["admin", "agent"] else "customer"

    # 创建消息
    chat_msg = ChatMessage(
        session_id=session_id,
        sender_id=current_user.id,
        sender_type=sender_type,
        content=message.get("content", ""),
        message_type=message.get("type", "text")
    )
    db.add(chat_msg)

    # 更新会话最后消息时间
    session.last_message_at = datetime.utcnow()
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取会话消息历史（分页加载）
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.id not in [session.customer_id, session.agent_id]:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 分页查询消息
    offset = (page - 1) * page_size
    messages_query = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc())  # 降序获取最新消息

    # 获取总数
    total = messages_query.count()

    # 分页获取消息
    messages = messages_query.offset(offset).limit(page_size).all()

    # 反转回正序（时间从旧到新）
    messages.reverse()

    return {
        "items": [{
            "id": m.id,
            "content": m.content,
            "sender_type": m.sender_type,
            "sender": {
                "id": m.sender_id,
                "name": m.sender.full_name or m.sender.username
            } if m.sender else None,
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
    session.closed_at = datetime.utcnow()
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