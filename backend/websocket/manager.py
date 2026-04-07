"""
WebSocket 连接管理器
"""
import logging
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

from utils.metrics import metrics

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 活动连接: user_id -> websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # 用户组: group_name -> set of user_ids
        self.groups: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """建立连接 - 注意：调用前需要先 await websocket.accept()"""
        self.active_connections[user_id] = websocket
        metrics.record_ws_connection(connected=True)
        logger.info(f"User connected, total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        metrics.record_ws_connection(connected=False)
        logger.info(f"User disconnected, remaining: {len(self.active_connections)}")

    async def send_personal_message(self, user_id: str, message: dict):
        """发送个人消息"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
            metrics.record_ws_message(sent=True)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)

    def add_to_group(self, group_name: str, user_id: str):
        """将用户添加到组"""
        if group_name not in self.groups:
            self.groups[group_name] = set()
        self.groups[group_name].add(user_id)

    def remove_from_group(self, group_name: str, user_id: str):
        """将用户从组移除"""
        if group_name in self.groups:
            self.groups[group_name].discard(user_id)

    async def broadcast_group(self, group_name: str, message: dict):
        """广播消息给组内所有用户"""
        if group_name in self.groups:
            for user_id in self.groups[group_name]:
                await self.send_personal_message(user_id, message)


# 全局连接管理器
ws_manager = ConnectionManager()


async def send_ticket_update(ticket_id: str, status: str, user_id: str):
    """发送工单更新通知"""
    message = {
        "type": "ticket_status_update",
        "ticket_id": ticket_id,
        "status": status,
        "timestamp": asyncio.get_event_loop().time()
    }
    await ws_manager.send_personal_message(user_id, message)


async def send_ticket_message(ticket_id: str, message: dict, user_id: str):
    """发送工单消息通知"""
    msg = {
        "type": "new_message",
        "ticket_id": ticket_id,
        "message": message,
        "timestamp": asyncio.get_event_loop().time()
    }
    await ws_manager.send_personal_message(user_id, msg)