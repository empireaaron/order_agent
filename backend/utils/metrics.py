"""
监控指标收集 - 支持数据库存储
用于跟踪 API 响应时间和 AI Agent 性能
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import timedelta, date
from uuid import uuid4
import logging

from utils.timezone import now

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器 - 线程安全单例

    支持内存统计和数据库持久化：
    - API 响应时间：仅内存（高频数据）
    - 意图识别：内存 + 数据库持久化
    - 错误统计：内存 + 数据库持久化
    - WebSocket：仅内存（连接状态）
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="metrics-")

        # API 响应时间统计 (最近 1000 条) - 仅内存
        self.api_latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # 意图识别统计 - 内存缓存
        self.intent_stats = {
            "total": 0,
            "correct": 0,
            "by_intent": defaultdict(lambda: {"total": 0, "correct": 0})
        }

        # 错误统计 - 仅内存
        self.error_counts: Dict[str, int] = defaultdict(int)
        self._error_keys_order: deque = deque(maxlen=100)

        # 操作计数器（用于触发内存清理）
        self._ops_counter = 0

        # WebSocket 连接统计 - 仅内存
        self.ws_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }

    def _get_db(self):
        """获取数据库会话（惰性导入避免循环依赖）"""
        try:
            from db.session import SessionLocal
            return SessionLocal()
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            return None

    def _save_intent_log_to_db(self, log_id: str, intent: str, user_input: str,
                                confidence: float = 1.0):
        """保存意图识别明细日志到数据库"""
        db = self._get_db()
        if not db:
            return

        try:
            from models import IntentClassificationLog

            log = IntentClassificationLog(
                id=log_id,
                metric_date=date.today(),
                intent=intent,
                user_input=user_input[:500] if user_input else None,  # 限制长度
                confidence=confidence,
                is_sampled=False,
                is_correct=None
            )
            db.add(log)
            db.commit()
            logger.debug(f"Saved intent log to DB: {log_id}, intent={intent}")

        except Exception as e:
            logger.error(f"Failed to save intent log: {e}")
            db.rollback()
        finally:
            db.close()

    def _save_intent_to_db(self, intent: str, is_correct: Optional[bool] = None,
                           confidence: float = 1.0):
        """保存意图识别记录到数据库"""
        db = self._get_db()
        if not db:
            return

        try:
            from models import IntentMetrics

            today = date.today()
            metric_id = f"{today.isoformat()}:{intent}"

            # 查询今天的记录
            record = db.query(IntentMetrics).filter(
                IntentMetrics.metric_date == today,
                IntentMetrics.intent == intent
            ).first()

            if record:
                # 更新现有记录
                record.total += 1
                record.confidence_sum += confidence
                if is_correct is not None and is_correct:
                    record.correct += 1
            else:
                # 创建新记录
                record = IntentMetrics(
                    id=str(uuid4()),
                    metric_date=today,
                    intent=intent,
                    total=1,
                    correct=1 if is_correct else 0,
                    confidence_sum=confidence,
                    sampled=0,
                    sampled_correct=0
                )
                db.add(record)

            db.commit()
            logger.debug(f"Saved intent metric to DB: {intent}, total={record.total}")

        except Exception as e:
            logger.error(f"Failed to save intent metric: {e}")
            db.rollback()
        finally:
            db.close()

    def _save_api_metric_to_db(self, endpoint: str, method: str,
                               latency_ms: float, is_error: bool = False):
        """保存 API 指标到数据库"""
        db = self._get_db()
        if not db:
            return

        try:
            from models import ApiMetrics

            today = date.today()
            metric_id = f"{today.isoformat()}:{method}:{endpoint}"

            # 查询今天的记录
            record = db.query(ApiMetrics).filter(
                ApiMetrics.metric_date == today,
                ApiMetrics.endpoint == endpoint,
                ApiMetrics.method == method
            ).first()

            if record:
                # 更新现有记录
                record.request_count += 1
                if is_error:
                    record.error_count += 1
                record.latency_sum_ms += latency_ms
                record.latency_min_ms = min(record.latency_min_ms, latency_ms) if record.latency_min_ms > 0 else latency_ms
                record.latency_max_ms = max(record.latency_max_ms, latency_ms)
            else:
                # 创建新记录
                record = ApiMetrics(
                    id=str(uuid4()),
                    metric_date=today,
                    endpoint=endpoint,
                    method=method,
                    request_count=1,
                    error_count=1 if is_error else 0,
                    latency_sum_ms=latency_ms,
                    latency_min_ms=latency_ms,
                    latency_max_ms=latency_ms
                )
                db.add(record)

            db.commit()

        except Exception as e:
            logger.error(f"Failed to save API metric: {e}")
            db.rollback()
        finally:
            db.close()

    def _save_error_to_db(self, error_type: str, endpoint: Optional[str] = None):
        """保存错误统计到数据库"""
        db = self._get_db()
        if not db:
            return

        try:
            from models import ErrorMetrics

            today = date.today()

            # 查询今天的记录
            record = db.query(ErrorMetrics).filter(
                ErrorMetrics.metric_date == today,
                ErrorMetrics.error_type == error_type,
                ErrorMetrics.endpoint == endpoint
            ).first()

            if record:
                record.count += 1
            else:
                record = ErrorMetrics(
                    id=str(uuid4()),
                    metric_date=today,
                    error_type=error_type,
                    endpoint=endpoint,
                    count=1
                )
                db.add(record)

            db.commit()

        except Exception as e:
            logger.error(f"Failed to save error metric: {e}")
            db.rollback()
        finally:
            db.close()

    def record_api_latency(self, endpoint: str, method: str, latency_ms: float):
        """记录 API 响应时间"""
        key = f"{method} {endpoint}"
        with self._lock:
            self.api_latencies[key].append({
                "timestamp": now(),
                "latency_ms": latency_ms
            })

        # 异步保存到数据库（不阻塞主流程）
        self._executor.submit(self._save_api_metric_to_db, endpoint, method, latency_ms, False)

    def _cleanup_memory_stats(self):
        """清理内存中的过期统计，防止无限增长"""
        # 限制意图类型数量
        if len(self.intent_stats["by_intent"]) > 50:
            # 保留统计量最大的 40 个意图
            sorted_intents = sorted(
                self.intent_stats["by_intent"].items(),
                key=lambda x: x[1]["total"],
                reverse=True
            )[:40]
            self.intent_stats["by_intent"] = defaultdict(
                lambda: {"total": 0, "correct": 0},
                dict(sorted_intents)
            )
            logger.debug("Cleaned up intent_stats memory cache")

        # 限制错误类型数量
        if len(self.error_counts) > 100:
            # 保留统计量最大的 80 个错误类型
            sorted_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:80]
            self.error_counts = defaultdict(int, dict(sorted_errors))
            self._error_keys_order.clear()
            self._error_keys_order.extend([k for k, _ in sorted_errors])
            logger.debug("Cleaned up error_counts memory cache")

    def record_intent_classification(self, intent: str, confidence: float = 1.0,
                                     is_correct: Optional[bool] = None,
                                     user_input: Optional[str] = None):
        """记录意图识别结果

        Args:
            intent: 识别的意图类型
            confidence: 置信度 (0-1)
            is_correct: 是否正确（可选，用于后续准确率计算）
            user_input: 用户输入内容（用于抽样标注）
        """
        # 生成唯一ID用于关联明细日志
        log_id = str(uuid4())

        # 更新内存统计
        with self._lock:
            self.intent_stats["total"] += 1
            self.intent_stats["by_intent"][intent]["total"] += 1

            if is_correct is not None:
                if is_correct:
                    self.intent_stats["correct"] += 1
                    self.intent_stats["by_intent"][intent]["correct"] += 1

            self._ops_counter += 1
            if self._ops_counter % 100 == 0:
                self._cleanup_memory_stats()

        # 异步保存到数据库（聚合统计）
        self._executor.submit(self._save_intent_to_db, intent, is_correct, confidence)

        # 异步保存明细日志（用于抽样标注）
        if user_input:
            self._executor.submit(self._save_intent_log_to_db, log_id, intent, user_input, confidence)

    def record_error(self, error_type: str, endpoint: Optional[str] = None):
        """记录错误"""
        key = f"{error_type}:{endpoint}" if endpoint else error_type
        with self._lock:
            self.error_counts[key] += 1
            if key not in self._error_keys_order:
                self._error_keys_order.append(key)

            self._ops_counter += 1
            if self._ops_counter % 100 == 0:
                self._cleanup_memory_stats()

        # 异步保存到数据库
        self._executor.submit(self._save_error_to_db, error_type, endpoint)

    def record_ws_connection(self, connected: bool = True):
        """记录 WebSocket 连接/断开（仅内存）"""
        with self._lock:
            if connected:
                self.ws_stats["total_connections"] += 1
                self.ws_stats["active_connections"] += 1
            else:
                self.ws_stats["active_connections"] = max(0, self.ws_stats["active_connections"] - 1)

    def record_ws_message(self, sent: bool = True):
        """记录 WebSocket 消息（仅内存）"""
        with self._lock:
            if sent:
                self.ws_stats["messages_sent"] += 1
            else:
                self.ws_stats["messages_received"] += 1

    def _fetch_api_stats_from_db(self, time_window_minutes: int) -> Dict[str, Any]:
        """从数据库获取 API 历史聚合数据（在线程池中执行）"""
        result = {}
        db = self._get_db()
        if not db:
            return result

        try:
            from models import ApiMetrics
            from sqlalchemy import func

            # 计算查询的起始日期（根据time_window_minutes）
            days_back = max(1, time_window_minutes // (24 * 60))
            start_date = date.today() - timedelta(days=days_back)

            db_stats = db.query(
                ApiMetrics.endpoint,
                ApiMetrics.method,
                func.sum(ApiMetrics.request_count).label('total_requests'),
                func.sum(ApiMetrics.error_count).label('total_errors'),
                func.sum(ApiMetrics.latency_sum_ms).label('total_latency'),
                func.min(ApiMetrics.latency_min_ms).label('min_latency'),
                func.max(ApiMetrics.latency_max_ms).label('max_latency')
            ).filter(
                ApiMetrics.metric_date >= start_date
            ).group_by(ApiMetrics.endpoint, ApiMetrics.method).all()

            for stat in db_stats:
                key = f"{stat.method} {stat.endpoint}"
                # 转换为 float 避免 decimal 类型错误
                total_latency = float(stat.total_latency) if stat.total_latency else 0
                total_requests = float(stat.total_requests) if stat.total_requests else 0
                result[key] = {
                    "count": int(stat.total_requests) if stat.total_requests else 0,
                    "error_count": int(stat.total_errors) if stat.total_errors else 0,
                    "avg_latency_ms": round(total_latency / total_requests, 2) if total_requests > 0 else 0,
                    "min_ms": round(float(stat.min_latency), 2) if stat.min_latency else 0,
                    "max_ms": round(float(stat.max_latency), 2) if stat.max_latency else 0,
                    "source": "db"
                }

        except Exception as e:
            logger.error(f"Failed to get DB API stats: {e}")
        finally:
            db.close()

        return result

    def get_api_stats(self, endpoint: Optional[str] = None,
                      time_window_minutes: int = 60) -> Dict[str, Any]:
        """获取 API 统计信息（内存 + 数据库）"""
        # 从内存获取实时数据
        cutoff_time = now() - timedelta(minutes=time_window_minutes)

        with self._lock:
            result = {}
            endpoints_to_check = [endpoint] if endpoint else list(self.api_latencies.keys())

            for ep in endpoints_to_check:
                latencies = [
                    r["latency_ms"] for r in self.api_latencies[ep]
                    if r["timestamp"] > cutoff_time
                ]

                if not latencies:
                    continue

                latencies.sort()
                n = len(latencies)

                result[ep] = {
                    "count": n,
                    "avg_latency_ms": round(sum(latencies) / n, 2),
                    "p50_ms": round(latencies[int(n * 0.5)], 2),
                    "p95_ms": round(latencies[int(n * 0.95)], 2),
                    "p99_ms": round(latencies[int(n * 0.99)], 2) if n >= 100 else round(latencies[-1], 2),
                    "max_ms": round(latencies[-1], 2)
                }

        # 从数据库获取历史聚合数据（放入线程池避免阻塞主线程）
        try:
            db_result = self._executor.submit(
                self._fetch_api_stats_from_db, time_window_minutes
            ).result(timeout=10)
            # 合并数据库结果，内存中已有的端点优先使用内存数据
            for key, value in db_result.items():
                if key not in result:
                    result[key] = value
        except Exception as e:
            logger.error(f"Failed to fetch API stats from DB in executor: {e}")

        return result

    def _fetch_intent_stats_from_db(self, days: int) -> Dict[str, Any]:
        """从数据库获取意图识别聚合数据（在线程池中执行）"""
        db_stats = {}
        db = self._get_db()
        if not db:
            return db_stats

        try:
            from models import IntentMetrics
            from sqlalchemy import func

            start_date = date.today() - timedelta(days=days)

            # 从数据库查询聚合数据
            results = db.query(
                IntentMetrics.intent,
                func.sum(IntentMetrics.total).label('total'),
                func.sum(IntentMetrics.correct).label('correct'),
                func.sum(IntentMetrics.sampled).label('sampled'),
                func.sum(IntentMetrics.sampled_correct).label('sampled_correct')
            ).filter(
                IntentMetrics.metric_date >= start_date
            ).group_by(IntentMetrics.intent).all()

            for r in results:
                db_stats[r.intent] = {
                    "total": r.total or 0,
                    "correct": r.correct or 0,
                    "sampled": r.sampled or 0,
                    "sampled_correct": r.sampled_correct or 0
                }

        except Exception as e:
            logger.error(f"Failed to get DB intent stats: {e}")
        finally:
            db.close()

        return db_stats

    def get_intent_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取意图识别统计（内存 + 数据库）

        Args:
            days: 查询最近几天的数据
        """
        # 从数据库获取历史聚合数据（放入线程池避免阻塞主线程）
        try:
            db_stats = self._executor.submit(
                self._fetch_intent_stats_from_db, days
            ).result(timeout=10)
        except Exception as e:
            logger.error(f"Failed to fetch intent stats from DB in executor: {e}")
            db_stats = {}

        # 合并内存中的今日数据
        with self._lock:
            total = sum(db_stats.get(k, {}).get("total", 0) for k in db_stats)
            correct = sum(db_stats.get(k, {}).get("correct", 0) for k in db_stats)

            # 加上今日内存数据
            total += self.intent_stats["total"]
            correct += self.intent_stats["correct"]

            stats = {
                "total_classifications": total,
                "accuracy": round(correct / total, 4) if total > 0 else 0,
                "period_days": days,
                "by_intent": {}
            }

            # 合并按意图统计
            all_intents = set(db_stats.keys()) | set(self.intent_stats["by_intent"].keys())
            for intent in all_intents:
                db_total = db_stats.get(intent, {}).get("total", 0)
                db_correct = db_stats.get(intent, {}).get("correct", 0)
                db_sampled = db_stats.get(intent, {}).get("sampled", 0)
                db_sampled_correct = db_stats.get(intent, {}).get("sampled_correct", 0)
                mem_total = self.intent_stats["by_intent"][intent]["total"]
                mem_correct = self.intent_stats["by_intent"][intent]["correct"]

                intent_total = db_total + mem_total
                intent_correct = db_correct + mem_correct

                stats["by_intent"][intent] = {
                    "total": intent_total,
                    "accuracy": round(intent_correct / intent_total, 4) if intent_total > 0 else 0,
                    "sampled": db_sampled,
                    "sampled_correct": db_sampled_correct,
                    "sampled_accuracy": round(db_sampled_correct / db_sampled, 4) if db_sampled > 0 else 0
                }

        return stats

    def _fetch_error_stats_from_db(self, days: int) -> Dict[str, int]:
        """从数据库获取错误统计数据（在线程池中执行）"""
        db_errors = {}
        db = self._get_db()
        if not db:
            return db_errors

        try:
            from models import ErrorMetrics
            from sqlalchemy import func

            start_date = date.today() - timedelta(days=days)

            results = db.query(
                ErrorMetrics.error_type,
                ErrorMetrics.endpoint,
                func.sum(ErrorMetrics.count).label('total')
            ).filter(
                ErrorMetrics.metric_date >= start_date
            ).group_by(ErrorMetrics.error_type, ErrorMetrics.endpoint).all()

            for r in results:
                key = f"{r.error_type}:{r.endpoint}" if r.endpoint else r.error_type
                db_errors[key] = r.total

        except Exception as e:
            logger.error(f"Failed to get DB error stats: {e}")
        finally:
            db.close()

        return db_errors

    def get_error_stats(self, days: int = 7) -> Dict[str, int]:
        """获取错误统计（内存 + 数据库）"""
        # 从数据库获取历史数据（放入线程池避免阻塞主线程）
        try:
            db_errors = self._executor.submit(
                self._fetch_error_stats_from_db, days
            ).result(timeout=10)
        except Exception as e:
            logger.error(f"Failed to fetch error stats from DB in executor: {e}")
            db_errors = {}

        # 合并内存中的今日数据
        with self._lock:
            for key, count in self.error_counts.items():
                db_errors[key] = db_errors.get(key, 0) + count

        return db_errors

    def get_ws_stats(self) -> Dict[str, Any]:
        """获取 WebSocket 统计（仅内存）"""
        with self._lock:
            return dict(self.ws_stats)

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        return {
            "timestamp": now().isoformat(),
            "api": self.get_api_stats(),
            "intent": self.get_intent_stats(),
            "errors": self.get_error_stats(),
            "websocket": self.get_ws_stats()
        }

    def reset(self):
        """重置所有统计（谨慎使用）"""
        with self._lock:
            self.api_latencies.clear()
            self.intent_stats = {
                "total": 0,
                "correct": 0,
                "by_intent": defaultdict(lambda: {"total": 0, "correct": 0})
            }
            self.error_counts.clear()
            self.ws_stats = {
                "total_connections": 0,
                "active_connections": 0,
                "messages_sent": 0,
                "messages_received": 0
            }


# 全局指标收集器实例
metrics = MetricsCollector()


class Timer:
    """计时器上下文管理器"""

    def __init__(self, name: str, collector: Optional[MetricsCollector] = None):
        self.name = name
        self.collector = collector or metrics
        self.start_time = None
        self.elapsed_ms = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        self.elapsed_ms = (end_time - self.start_time) * 1000

        if exc_type is not None:
            self.collector.record_error(exc_type.__name__)

        return False