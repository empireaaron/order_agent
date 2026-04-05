"""
实时聊天 WebSocket 处理
"""
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from datetime import datetime

from models.chat import ChatSession, ChatMessage, AgentStatus
from db.session import SessionLocal


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
        print(f"Chat user {user_id_str} connected, total connections: {len(self.user_connections)}")

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
                    print(f"User {user_id_str} removed from session {session_id} as {role}")
            # 如果会话为空，删除会话
            if not self.session_users[session_id]:
                del self.session_users[session_id]

        print(f"Chat user {user_id_str} disconnected, remaining connections: {len(self.user_connections)}")

    async def auto_join_sessions(self, user_id: str):
        """自动加入用户进行中的会话"""
        db = SessionLocal()
        try:
            # 查询用户进行中的会话
            sessions = db.query(ChatSession).filter(
                ((ChatSession.customer_id == user_id) | (ChatSession.agent_id == user_id)),
                ChatSession.status == "connected"
            ).all()

            print(f"DEBUG auto_join_sessions for {user_id}: found {len(sessions)} active sessions")

            for session in sessions:
                session_id = str(session.id)
                # 确定用户角色
                if str(session.customer_id) == user_id:
                    role = "customer"
                elif str(session.agent_id) == user_id:
                    role = "agent"
                else:
                    continue

                # 加入会话
                self.join_session(session_id, user_id, role)

                # 通知用户已重新加入会话
                await self.send_to_user(user_id, {
                    "type": "session_rejoined",
                    "session_id": session_id,
                    "role": role,
                    "message": "已重新连接到会话"
                })
                print(f"DEBUG auto-joined user {user_id} to session {session_id} as {role}")
        finally:
            db.close()

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给指定用户"""
        user_id_str = str(user_id)
        print(f"DEBUG send_to_user: target={user_id_str}, connections={list(self.user_connections.keys())}")
        if user_id_str in self.user_connections:
            try:
                await self.user_connections[user_id_str].send_json(message)
                print(f"DEBUG message sent to user {user_id_str}")
            except Exception as e:
                print(f"Error sending to user {user_id_str}: {e}")
        else:
            print(f"DEBUG user {user_id_str} not in connections")

    async def send_to_session(self, session_id: str, message: dict, exclude_user: str = None):
        """发送消息给会话中的所有用户"""
        session_id_str = str(session_id)
        exclude_str = str(exclude_user) if exclude_user else None

        print(f"DEBUG send_to_session: session_id={session_id_str}")
        print(f"DEBUG session_users: {self.session_users}")

        if session_id_str not in self.session_users:
            print(f"DEBUG session {session_id_str} not found")
            return

        users = self.session_users[session_id_str]
        print(f"DEBUG users in session: {users}")

        for role, user_id in users.items():
            user_id_str = str(user_id)
            print(f"DEBUG processing role={role}, user_id={user_id_str}")

            # 跳过被排除的用户
            if exclude_str and user_id_str == exclude_str:
                print(f"DEBUG excluding {user_id_str}")
                continue

            print(f"DEBUG sending to {user_id_str}")
            await self.send_to_user(user_id_str, message)

    async def broadcast_all(self, message: dict, exclude_user: str = None):
        """广播消息给所有在线用户"""
        for user_id, websocket in self.user_connections.items():
            if user_id != exclude_user:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to user {user_id}: {e}")

    async def broadcast_to_agents(self, message: dict, exclude_user: str = None):
        """广播消息给所有在线客服"""
        from db.session import SessionLocal
        from models.chat import AgentStatus

        db = SessionLocal()
        try:
            # 获取所有在线客服的ID
            agent_statuses = db.query(AgentStatus).filter(
                AgentStatus.status == "online"
            ).all()

            print(f"DEBUG: Found {len(agent_statuses)} online agents")
            print(f"DEBUG: Current connections: {list(self.user_connections.keys())}")

            for status in agent_statuses:
                agent_id = str(status.agent_id)  # 确保是字符串
                exclude_id = str(exclude_user) if exclude_user else None

                print(f"DEBUG: Checking agent {agent_id}, in connections: {agent_id in self.user_connections}")

                if agent_id != exclude_id and agent_id in self.user_connections:
                    try:
                        await self.user_connections[agent_id].send_json(message)
                        print(f"DEBUG: Broadcasted to agent {agent_id}")
                    except Exception as e:
                        print(f"Error broadcasting to agent {agent_id}: {e}")
        finally:
            db.close()

    def join_session(self, session_id: str, user_id: str, role: str):
        """用户加入会话"""
        user_id_str = str(user_id)
        if session_id not in self.session_users:
            self.session_users[session_id] = {}
        self.session_users[session_id][role] = user_id_str
        print(f"User {user_id_str} joined session {session_id} as {role}")
        print(f"DEBUG current session_users: {self.session_users}")

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
        print(f"DEBUG handle_message from {user_id_str}: type={msg_type}")

        if msg_type == "join_session":
            # 加入会话
            session_id = data.get("session_id")
            role = data.get("role", "customer")
            print(f"DEBUG joining session {session_id} as {role}")
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
            print(f"DEBUG chat_message from {user_id_str}, session {session_id}: {content}")

            # 保存到数据库
            db = SessionLocal()
            try:
                session = db.query(ChatSession).filter(
                    ChatSession.id == session_id
                ).first()

                if session:
                    # 确定发送者类型 - 统一使用字符串比较
                    session_agent_id = str(session.agent_id) if session.agent_id else None
                    sender_type = "agent" if user_id_str == session_agent_id else "customer"
                    print(f"DEBUG sender_type={sender_type}, session.agent_id={session_agent_id}, user_id={user_id_str}")

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
                    print(f"DEBUG broadcasting message to session {session_id}, exclude {user_id_str}")
                    await self.send_to_session(session_id, broadcast_msg, exclude_user=user_id_str)
                else:
                    print(f"DEBUG session {session_id} not found")
            finally:
                db.close()

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

            db = SessionLocal()
            try:
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
            finally:
                db.close()


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