"""
短期记忆管理 - 存储用户的对话历史（带自动摘要的平衡方案）

支持两种存储后端：
1. 内存存储（默认，单实例）
2. Redis 存储（分布式部署）

实现 ConversationSummaryBufferMemory 逻辑：
- 保留最近 N 条消息原文
- 对早期消息自动生成摘要
- 适合长对话场景
"""
import threading
import time
from collections import defaultdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from config import settings


class ShortTermMemory:
    """短期记忆管理器 - 按用户存储对话历史，支持自动摘要，支持多后端（线程安全单例）"""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, backend: str = "auto"):
        """线程安全单例模式

        Args:
            backend: 存储后端 ("auto", "memory", "redis")
                - "auto": 自动检测，优先使用 Redis（如果可用）
                - "memory": 强制使用内存
                - "redis": 强制使用 Redis
        """
        if cls._instance is None:
            with cls._lock:
                # 双重检查锁定
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._init_storage(backend)
                    cls._instance = instance
        return cls._instance

    def _init_storage(self, backend: str = "auto"):
        """初始化存储"""
        self._memory_storage = None
        self._redis_storage = None
        self._backend = "memory"  # 默认后端

        # 配置（从 settings 读取，支持环境变量配置）
        self.max_messages = settings.STM_MAX_MESSAGES
        self.buffer_size = settings.STM_BUFFER_SIZE
        self.summary_trigger = settings.STM_SUMMARY_TRIGGER
        self.expire_seconds = settings.STM_EXPIRE_SECONDS

        # 选择后端
        if backend == "auto":
            # 尝试 Redis，失败则回退到内存
            try:
                from memory.redis_store import redis_store
                if redis_store.is_available():
                    self._redis_storage = redis_store
                    self._backend = "redis"
                    print("[INFO] 使用 Redis 存储后端")
                else:
                    self._init_memory_backend()
            except Exception as e:
                print(f"[WARNING] Redis 初始化失败，回退到内存: {e}")
                self._init_memory_backend()
        elif backend == "redis":
            from memory.redis_store import redis_store
            if redis_store.is_available():
                self._redis_storage = redis_store
                self._backend = "redis"
                print("[INFO] 使用 Redis 存储后端（强制）")
            else:
                raise RuntimeError("Redis 不可用，但强制指定了 redis 后端")
        else:
            self._init_memory_backend()

    def _init_memory_backend(self):
        """初始化内存后端"""
        self._memory_storage = defaultdict(
            lambda: {"messages": [], "summary": "", "last_summary_time": 0}
        )
        self._backend = "memory"
        print("[INFO] 使用内存存储后端")

    def _is_redis(self) -> bool:
        """是否使用 Redis 后端"""
        return self._backend == "redis" and self._redis_storage is not None

    def add_message(self, user_id: str, role: str, content: str):
        """
        添加消息到用户记忆

        Args:
            user_id: 用户ID
            role: 角色 (human/ai/system)
            content: 消息内容
        """
        if not user_id:
            return

        # Redis 模式
        if self._is_redis():
            self._redis_storage.add_message(user_id, role, content, self.expire_seconds)
            # 检查是否需要生成摘要（Redis 模式下在内存中计算）
            messages = self._redis_storage.get_messages(user_id, limit=100)
            if len(messages) >= self.summary_trigger:
                self._generate_redis_summary(user_id, messages)
            return

        # 内存模式
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }

        user_data = self._memory_storage[user_id]
        user_data["messages"].append(message)

        # 清理过期消息
        self._cleanup_expired(user_id)

        # 检查是否需要生成摘要
        if len(user_data["messages"]) >= self.summary_trigger:
            self._generate_summary(user_id)

        # 保持消息数量在限制内
        self._prune_messages(user_id)

    def _generate_summary(self, user_id: str):
        """为内存模式生成摘要"""
        user_data = self._memory_storage[user_id]
        messages = user_data["messages"]

        if len(messages) <= self.buffer_size:
            return

        # 需要摘要的消息（除最近 buffer_size 条之外的所有消息）
        messages_to_summarize = messages[:-self.buffer_size]
        recent_messages = messages[-self.buffer_size:]

        # 生成摘要
        try:
            summary = self._create_summary(messages_to_summarize, user_data.get("summary", ""))
            user_data["summary"] = summary
            user_data["last_summary_time"] = time.time()

            # 替换为：摘要 + 保留的原文
            user_data["messages"] = [
                {"role": "system", "content": f"[历史对话摘要] {summary}", "timestamp": time.time(), "is_summary": True}
            ] + recent_messages

            print(f"[DEBUG] 为用户 {user_id} 生成对话摘要，保留最近 {len(recent_messages)} 条原文")

        except Exception as e:
            print(f"[ERROR] 生成摘要失败: {e}")
            user_data["messages"] = messages[-self.max_messages:]

    def _generate_redis_summary(self, user_id: str, messages: List[Dict]):
        """为 Redis 模式生成摘要"""
        if len(messages) <= self.buffer_size:
            return

        # 检查是否已有摘要
        existing_summary = self._redis_storage.get_summary(user_id)
        if existing_summary:
            return  # 已有摘要，不再生成

        # 生成摘要
        try:
            messages_to_summarize = messages[:-self.buffer_size]
            summary = self._create_summary(messages_to_summarize, "")

            # 保存摘要到 Redis
            self._redis_storage.save_summary(user_id, summary, self.expire_seconds)
            print(f"[DEBUG] 为用户 {user_id} 生成 Redis 摘要")

        except Exception as e:
            print(f"[ERROR] Redis 生成摘要失败: {e}")

    def _create_summary(self, messages: List[Dict], existing_summary: str) -> str:
        """创建对话摘要"""
        key_points = []

        # 统计信息
        human_msgs = [m for m in messages if m.get("role") == "human"]

        # 提取用户的主要问题
        for msg in human_msgs[-3:]:  # 最近3个用户问题
            content = msg.get("content", "")[:100]
            if len(content) > 30:
                key_points.append(f"用户询问: {content}...")

        # 如果有已有摘要，合并
        if existing_summary:
            key_points.insert(0, f" earlier: {existing_summary[:200]}...")

        if not key_points:
            return "用户进行了简短对话"

        return "; ".join(key_points[:3])

    def _prune_messages(self, user_id: str):
        """修剪消息数量，保持在限制范围内"""
        if self._is_redis():
            return  # Redis 自动过期，不需要修剪

        user_data = self._memory_storage[user_id]
        messages = user_data["messages"]

        if len(messages) > self.max_messages:
            if messages and messages[0].get("is_summary"):
                user_data["messages"] = [messages[0]] + messages[-(self.max_messages - 1):]
            else:
                user_data["messages"] = messages[-self.max_messages:]

    def get_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户的历史消息"""
        if not user_id:
            return []

        if self._is_redis():
            messages = self._redis_storage.get_messages(user_id, limit)
            summary = self._redis_storage.get_summary(user_id)
            if summary and messages:
                # 在开头添加摘要
                summary_msg = {"role": "system", "content": f"[历史对话摘要] {summary}", "is_summary": True, "timestamp": 0}
                return [summary_msg] + messages
            return messages

        # 内存模式
        self._cleanup_expired(user_id)
        user_data = self._memory_storage[user_id]
        messages = user_data["messages"]
        return messages[-limit:] if messages else []

    def get_messages_with_summary(self, user_id: str) -> tuple[List[Dict[str, Any]], str]:
        """获取消息和摘要"""
        if self._is_redis():
            messages = self._redis_storage.get_messages(user_id, limit=100)
            summary = self._redis_storage.get_summary(user_id)
            return messages, summary

        # 内存模式
        self._cleanup_expired(user_id)
        user_data = self._memory_storage[user_id]
        return user_data["messages"], user_data.get("summary", "")

    def get_messages_as_lc(self, user_id: str, limit: int = 10) -> List[BaseMessage]:
        """获取用户历史消息并转换为LangChain消息格式"""
        messages = self.get_messages(user_id, limit)
        lc_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "human":
                lc_messages.append(HumanMessage(content=content))
            elif role == "ai":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        return lc_messages

    def clear_memory(self, user_id: str):
        """清空用户记忆"""
        if self._is_redis():
            self._redis_storage.clear_memory(user_id)
            return

        if user_id in self._memory_storage:
            del self._memory_storage[user_id]

    def clear_all_memory(self):
        """清空所有记忆"""
        if self._is_redis():
            self._redis_storage.clear_all_memory()
            return

        self._memory_storage.clear()

    def _cleanup_expired(self, user_id: str):
        """清理过期消息（仅内存模式）"""
        if self._is_redis() or user_id not in self._memory_storage:
            return

        user_data = self._memory_storage[user_id]
        messages = user_data["messages"]

        if messages:
            last_msg_time = messages[-1].get("timestamp", 0)
            if last_msg_time < time.time() - self.expire_seconds:
                user_data["messages"] = []
                user_data["summary"] = ""
                user_data["last_summary_time"] = 0
                print(f"[DEBUG] 用户 {user_id} 的对话已过期，清空记忆")

    def get_conversation_summary(self, user_id: str) -> str:
        """获取对话摘要（用于调试）"""
        if self._is_redis():
            messages = self._redis_storage.get_messages(user_id, limit=100)
            summary = self._redis_storage.get_summary(user_id)
            lines = []
            if summary:
                lines.append(f"【摘要】{summary[:100]}...")
                lines.append("")
            for msg in messages[-10:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:50]
                lines.append(f"{role}: {content}...")
            return "\n".join(lines)

        # 内存模式
        if user_id not in self._memory_storage:
            return "无历史对话"

        user_data = self._memory_storage[user_id]
        messages = user_data["messages"]
        summary = user_data.get("summary", "")

        lines = []
        if summary:
            lines.append(f"【摘要】{summary[:100]}...")
            lines.append("")

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]
            timestamp = msg.get("timestamp", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            marker = "[摘]" if msg.get("is_summary") else ""
            lines.append(f"[{time_str}] {marker} {role}: {content}...")

        return "\n".join(lines)

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        if self._is_redis():
            messages = self._redis_storage.get_messages(user_id, limit=100)
            summary = self._redis_storage.get_summary(user_id)
            return {
                "backend": "redis",
                "total_messages": len(messages),
                "has_summary": bool(summary),
                "summary_length": len(summary) if summary else 0,
            }

        # 内存模式
        if user_id not in self._memory_storage:
            return {"backend": "memory", "total_messages": 0, "has_summary": False}

        user_data = self._memory_storage[user_id]
        messages = user_data["messages"]
        summary = user_data.get("summary", "")

        return {
            "backend": "memory",
            "total_messages": len(messages),
            "has_summary": bool(summary),
            "summary_length": len(summary),
            "buffer_size": self.buffer_size,
            "max_messages": self.max_messages,
            "human_messages": len([m for m in messages if m.get("role") == "human"]),
            "ai_messages": len([m for m in messages if m.get("role") == "ai"]),
        }

    def get_backend(self) -> str:
        """获取当前后端类型"""
        return self._backend


# 全局记忆实例（自动检测后端）
short_term_memory = ShortTermMemory(backend="auto")