"""
Redis 存储后端 - 支持分布式部署
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis 包未安装，Redis 存储不可用。请运行: pip install redis")


class RedisMemoryStore:
    """Redis 存储后端"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        """初始化 Redis 客户端"""
        if not REDIS_AVAILABLE:
            self.client = None
            return

        try:
            from config import settings
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self.client.ping()
            logger.info("Redis 连接成功: %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)
        except Exception as e:
            logger.error("Redis 连接失败: %s", e)
            self.client = None

    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        if not REDIS_AVAILABLE or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def _get_key(self, user_id: str, suffix: str = "messages") -> str:
        """生成 Redis key"""
        return f"chat_memory:{user_id}:{suffix}"

    def add_message(self, user_id: str, role: str, content: str, expire_seconds: int = 1800):
        """添加消息"""
        if not self.is_available():
            return False

        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": time.time()
            }
            key = self._get_key(user_id)
            # 使用列表存储消息
            self.client.rpush(key, json.dumps(message))
            # 设置过期时间
            self.client.expire(key, expire_seconds)
            return True
        except Exception as e:
            logger.error("Redis add_message 失败: %s", e)
            return False

    def get_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取消息列表"""
        if not self.is_available():
            return []

        try:
            key = self._get_key(user_id)
            # 获取最近的消息
            raw_messages = self.client.lrange(key, -limit, -1)
            messages = []
            for raw in raw_messages:
                try:
                    msg = json.loads(raw)
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue
            return messages
        except Exception as e:
            logger.error("Redis get_messages 失败: %s", e)
            return []

    def clear_memory(self, user_id: str):
        """清空用户记忆"""
        if not self.is_available():
            return False

        try:
            key_messages = self._get_key(user_id, "messages")
            key_summary = self._get_key(user_id, "summary")
            self.client.delete(key_messages, key_summary)
            return True
        except Exception as e:
            logger.error("Redis clear_memory 失败: %s", e)
            return False

    def clear_all_memory(self):
        """清空所有记忆（慎用）"""
        if not self.is_available():
            return False

        try:
            # 删除所有 chat_memory:* 的 key
            keys = self.client.keys("chat_memory:*")
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            logger.error("Redis clear_all_memory 失败: %s", e)
            return False

    def save_summary(self, user_id: str, summary: str, expire_seconds: int = 1800):
        """保存摘要"""
        if not self.is_available():
            return False

        try:
            key = self._get_key(user_id, "summary")
            self.client.set(key, summary, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error("Redis save_summary 失败: %s", e)
            return False

    def get_summary(self, user_id: str) -> str:
        """获取摘要"""
        if not self.is_available():
            return ""

        try:
            key = self._get_key(user_id, "summary")
            summary = self.client.get(key)
            return summary or ""
        except Exception as e:
            logger.error("Redis get_summary 失败: %s", e)
            return ""

    def get_all_keys(self, pattern: str = "chat_memory:*") -> List[str]:
        """获取所有匹配的 key（用于调试）"""
        if not self.is_available():
            return []

        try:
            return list(self.client.scan_iter(match=pattern))
        except Exception as e:
            logger.error("Redis get_all_keys 失败: %s", e)
            return []


# 全局 Redis 实例
redis_store = RedisMemoryStore()