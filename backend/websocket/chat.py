"""
实时聊天 WebSocket 处理
"""
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from models.chat import ChatSession, ChatMessage, AgentStatus
from db.session import get_db_context

logger = logging.getLogger(__name__)


class ChatWebSocketManager:
    """聊天WebSocket管理器"""

    def __init__(self):
        # 用户连接: user_id -> websocket
        self.user_connections: Dict[str, WebSocket] = {}
        # 会话中的用户: session_id -> {customer_id, agent_id}
        self.session_users: Dict[str, Dict[str, str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """用户连接 - 注意：调用前需要先 await websocket.accept()"""
        user_id_str = str(user_id)
        self.user_connections[user_id_str] = websocket
        logger.info(f"Chat user connected, total connections: {len(self.user_connections)}")

        # 检查用户是否有进行中的会话，如果有则自动加入
        await self.auto_join_sessions(user_id_str)

    def disconnect(self, user_id: str):
        """用户断开"""
        user_id_str = str(user_id)
        # 从连接列表中移除
        if user_id_str in self.user_connections:
            del self.user_connections[user_id_str]

        # 从所有会话中移除该用户
        for session_id in list(self.session_users.keys()):
            for role, uid in list(self.session_users[session_id].items()):
                if uid == user_id_str:
                    del self.session_users[session_id][role]
                    logger.debug(f"User removed from session {session_id} as {role}")
            # 如果会话为空，删除会话
            if not self.session_users[session_id]:
                del self.session_users[session_id]

        logger.info(f"Chat user disconnected, remaining connections: {len(self.user_connections)}")

    async def auto_join_sessions(self, user_id: str):
        """自动加入用户进行中的会话（包括最近关闭的）"""
        from datetime import datetime, timedelta

        with get_db_context() as db:
            # 查询用户进行中的会话，以及24小时内关闭的会话
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            sessions = db.query(ChatSession).filter(
                ((ChatSession.customer_id == user_id) | (ChatSession.agent_id == user_id)),
                ((ChatSession.status == "connected") |
                 ((ChatSession.status == "closed") & (ChatSession.closed_at >= cutoff_time)))
            ).all()

            logger.info(f"auto_join_sessions: user={user_id}, found {len(sessions)} sessions")
            for s in sessions:
                logger.info(f"  session {s.id}: status={s.status}, closed_at={s.closed_at}")

            # 优先处理进行中的会话，如果没有则处理最近关闭的会话
            active_session = None
            closed_session = None

            for session in sessions:
                if session.status == "connected":
                    active_session = session
                    break  # 找到进行中的会话，立即停止
                elif session.status == "closed" and closed_session is None:
                    closed_session = session  # 记录第一个关闭的会话

            # 处理选中的会话
            session = active_session or closed_session
            if session:
                session_id = str(session.id)
                # 确定用户角色
                if str(session.customer_id) == user_id:
                    role = "customer"
                elif str(session.agent_id) == user_id:
                    role = "agent"
                else:
                    return

                # 根据会话状态处理
                logger.info(f"Processing session {session_id}, status={session.status}, role={role}")
                if session.status == "closed":
                    # 已关闭的会话：不加入，只通知客户端加载历史
                    await self.send_to_user(user_id, {
                        "type": "session_history",
                        "session_id": session_id,
                        "role": role,
                        "status": "closed",
                        "message": "会话已结束，以下是历史记录"
                    })
                    logger.info(f"Sent session_history for closed session {session_id}")
                else:
                    # 进行中的会话：加入会话
                    self.join_session(session_id, user_id, role)

                    # 通知用户已重新加入会话
                    await self.send_to_user(user_id, {
                        "type": "session_rejoined",
                        "session_id": session_id,
                        "role": role,
                        "status": session.status,
                        "message": "已重新连接到会话"
                    })
                    logger.info(f"Sent session_rejoined for active session {session_id}")

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给指定用户"""
        user_id_str = str(user_id)
        logger.debug(f"send_to_user: {len(self.user_connections)} connections")
        if user_id_str in self.user_connections:
            try:
                await self.user_connections[user_id_str].send_json(message)
                logger.debug("message sent to user")
            except Exception as e:
                logger.error(f"Error sending to user: {e}")
        else:
            logger.debug("user not in connections")

    async def send_to_session(self, session_id: str, message: dict, exclude_user: str = None):
        """发送消息给会话中的所有用户"""
        session_id_str = str(session_id)
        exclude_str = str(exclude_user) if exclude_user else None

        logger.debug(f"send_to_session: session_id={session_id_str}")

        if session_id_str not in self.session_users:
            logger.debug(f"session {session_id_str} not found")
            return

        users = self.session_users[session_id_str]
        logger.debug(f"users in session: {len(users)} users")

        for role, user_id in users.items():
            user_id_str = str(user_id)
            logger.debug(f"processing role={role}")

            # 跳过被排除的用户
            if exclude_str and user_id_str == exclude_str:
                logger.debug("excluding sender from broadcast")
                continue

                logger.debug("sending message")
            await self.send_to_user(user_id_str, message)

    async def broadcast_all(self, message: dict, exclude_user: str = None):
        """广播消息给所有在线用户"""
        for user_id, websocket in self.user_connections.items():
            if user_id != exclude_user:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user: {e}")

    async def broadcast_to_agents(self, message: dict, exclude_user: str = None):
        """广播消息给所有在线客服"""
        from models.chat import AgentStatus

        with get_db_context() as db:
            # 获取所有在线客服的ID
            agent_statuses = db.query(AgentStatus).filter(
                AgentStatus.status == "online"
            ).all()

            logger.debug(f"Found {len(agent_statuses)} online agents, {len(self.user_connections)} connections")

            for status in agent_statuses:
                agent_id = str(status.agent_id)  # 确保是字符串
                exclude_id = str(exclude_user) if exclude_user else None

                logger.debug(f"Checking agent availability")

                if agent_id != exclude_id and agent_id in self.user_connections:
                    try:
                        await self.user_connections[agent_id].send_json(message)
                        logger.debug("Broadcasted to agent")
                    except Exception as e:
                        logger.error(f"Error broadcasting to agent: {e}")

    def join_session(self, session_id: str, user_id: str, role: str):
        """用户加入会话"""
        user_id_str = str(user_id)
        if session_id not in self.session_users:
            self.session_users[session_id] = {}
        self.session_users[session_id][role] = user_id_str
        logger.info(f"User joined session {session_id}")
        logger.debug(f"Session users updated: {len(self.session_users)} sessions")

    def leave_session(self, session_id: str, user_id: str):
        """用户离开会话"""
        if session_id in self.session_users:
            for role, uid in list(self.session_users[session_id].items()):
                if uid == user_id:
                    del self.session_users[session_id][role]
            if not self.session_users[session_id]:
                del self.session_users[session_id]

    async def handle_message(self, user_id: str, data: dict):
        """处理收到的消息"""
        msg_type = data.get("type")

        user_id_str = str(user_id)
        # 记录消息接收
        from utils.metrics import metrics
        metrics.record_ws_message(sent=False)
        logger.debug(f"handle_message: type={msg_type}")

        if msg_type == "join_session":
            # 加入会话
            session_id = data.get("session_id")
            role = data.get("role", "customer")
            logger.debug(f"Joining session {session_id}")
            self.join_session(session_id, user_id_str, role)

            await self.send_to_user(user_id_str, {
                "type": "joined",
                "session_id": session_id,
                "role": role
            })

        elif msg_type == "chat_message":
            # 聊天消息
            session_id = data.get("session_id")
            content = data.get("content")
            logger.debug(f"Chat message in session {session_id}")

            # 保存到数据库
            with get_db_context() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.id == session_id
                ).first()

                if session:
                    # 确定发送者类型 - 统一使用字符串比较
                    session_agent_id = str(session.agent_id) if session.agent_id else None
                    sender_type = "agent" if user_id_str == session_agent_id else "customer"
                    logger.debug(f"Processing message with sender_type={sender_type}")

                    # 获取发送者信息
                    from models import User
                    sender = db.query(User).filter(User.id == user_id).first()
                    sender_name = sender.full_name or sender.username if sender else "Unknown"

                    # 保存消息
                    msg = ChatMessage(
                        session_id=session_id,
                        sender_id=user_id_str,
                        sender_type=sender_type,
                        content=content
                    )
                    db.add(msg)

                    # 更新会话最后消息时间
                    session.last_message_at = datetime.utcnow()
                    db.commit()
                    db.refresh(msg)

                    # 广播给会话中的所有用户
                    broadcast_msg = {
                        "type": "new_message",
                        "session_id": session_id,
                        "message": {
                            "id": msg.id,
                            "content": content,
                            "sender_type": sender_type,
                            "sender_id": user_id_str,
                            "sender": {
                                "id": user_id_str,
                                "name": sender_name
                            },
                            "created_at": msg.created_at.isoformat()
                        }
                    }
                    logger.debug(f"Broadcasting message to session {session_id}")
                    await self.send_to_session(session_id, broadcast_msg, exclude_user=user_id_str)
                else:
                    logger.debug(f"Session {session_id} not found")

        elif msg_type == "typing":
            # 正在输入
            session_id = data.get("session_id")
            await self.send_to_session(session_id, {
                "type": "typing",
                "session_id": session_id,
                "user_id": user_id_str
            }, exclude_user=user_id_str)

        elif msg_type == "read":
            # 标记已读
            session_id = data.get("session_id")
            message_ids = data.get("message_ids", [])

            with get_db_context() as db:
                for msg_id in message_ids:
                    msg = db.query(ChatMessage).filter(
                        ChatMessage.id == msg_id
                    ).first()
                    if msg:
                        msg.is_read = "1"
                        msg.read_at = datetime.utcnow()
                db.commit()

                # 通知对方已读
                await self.send_to_session(session_id, {
                    "type": "read_receipt",
                    "session_id": session_id,
                    "message_ids": message_ids
                }, exclude_user=user_id_str)

        elif msg_type == "ping":
            # 心跳响应
            await self.send_to_user(user_id_str, {"type": "pong"})


# 全局聊天WebSocket管理器
chat_ws_manager = ChatWebSocketManager()


async def notify_new_session(session_id: str, customer_info: dict):
    """通知所有在线客服有新会话"""
    await chat_ws_manager.send_to_session("admin_broadcast", {
        "type": "new_waiting_session",
        "session_id": session_id,
        "customer": customer_info,
        "created_at": datetime.utcnow().isoformat()
    })


async def notify_session_assigned(session_id: str, agent_info: dict, customer_id: str):
    """通知客户已被接入"""
    await chat_ws_manager.send_to_user(customer_id, {
        "type": "session_assigned",
        "session_id": session_id,
        "agent": agent_info
    })