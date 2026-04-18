"""
WebSocket 连接管理器
"""
import logging
import asyncio
from typing import Dict, Set, List
from fastapi import WebSocket, WebSocketDisconnect

from utils.metrics import metrics

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 活动连接: user_id -> list of websockets（支持同一用户多端登录）
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # 用户组: group_name -> set of user_ids
        self.groups: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str):
        """建立连接 - 注意：调用前需要先 await websocket.accept()"""
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
        metrics.record_ws_connection(connected=True)
        logger.info(f"User connected, total connections: {self._total_connections()}")

    async def disconnect(self, user_id: str, websocket: WebSocket = None):
        """断开连接"""
        async with self._lock:
            if user_id in self.active_connections:
                if websocket and websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                else:
                    self.active_connections[user_id] = []
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
        metrics.record_ws_connection(connected=False)
        logger.info(f"User disconnected, remaining: {self._total_connections()}")

    def _total_connections(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    async def send_personal_message(self, user_id: str, message: dict):
        """发送个人消息给该用户的所有连接"""
        async with self._lock:
            connections = list(self.active_connections.get(user_id, []))
        for websocket in connections:
            try:
                await websocket.send_json(message)
                metrics.record_ws_message(sent=True)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                await self.disconnect(user_id, websocket)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        async with self._lock:
            all_connections = [
                (user_id, ws)
                for user_id, conns in self.active_connections.items()
                for ws in conns
            ]
        for user_id, websocket in all_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                await self.disconnect(user_id, websocket)

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