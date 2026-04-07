"""
监控指标数据模型
用于持久化存储 AI Agent 意图识别统计等信息
"""
from sqlalchemy import Column, String, Integer, Date, DateTime, Float, Index
from sqlalchemy.sql import func
from datetime import date

from db.session import Base


class IntentMetrics(Base):
    """意图识别统计 - 按天聚合"""
    __tablename__ = "intent_metrics"

    id = Column(String(36), primary_key=True)
    metric_date = Column(Date, nullable=False, index=True)  # 统计日期
    intent = Column(String(50), nullable=False, index=True)  # 意图类型
    total = Column(Integer, default=0, nullable=False)  # 总识别次数
    correct = Column(Integer, default=0, nullable=False)  # 正确次数
    confidence_sum = Column(Float, default=0.0)  # 置信度总和（用于计算平均置信度）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_intent_metrics_date_intent', 'metric_date', 'intent', unique=True),
    )

    @property
    def accuracy(self) -> float:
        """计算准确率"""
        if self.total == 0:
            return 0.0
        return self.correct / self.total

    @property
    def avg_confidence(self) -> float:
        """计算平均置信度"""
        if self.total == 0:
            return 0.0
        return self.confidence_sum / self.total


class ApiMetrics(Base):
    """API 响应时间统计 - 按天、按端点聚合"""
    __tablename__ = "api_metrics"

    id = Column(String(36), primary_key=True)
    metric_date = Column(Date, nullable=False, index=True)
    endpoint = Column(String(255), nullable=False, index=True)  # 端点路径
    method = Column(String(10), nullable=False)  # HTTP 方法
    request_count = Column(Integer, default=0, nullable=False)  # 请求次数
    error_count = Column(Integer, default=0, nullable=False)  # 错误次数（4xx/5xx）
    latency_sum_ms = Column(Float, default=0.0)  # 总响应时间（毫秒）
    latency_min_ms = Column(Float, default=0.0)  # 最小响应时间
    latency_max_ms = Column(Float, default=0.0)  # 最大响应时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_api_metrics_date_endpoint', 'metric_date', 'endpoint', 'method', unique=True),
    )

    @property
    def avg_latency_ms(self) -> float:
        """计算平均响应时间"""
        if self.request_count == 0:
            return 0.0
        return self.latency_sum_ms / self.request_count


class ErrorMetrics(Base):
    """错误统计 - 按天、按错误类型聚合"""
    __tablename__ = "error_metrics"

    id = Column(String(36), primary_key=True)
    metric_date = Column(Date, nullable=False, index=True)
    error_type = Column(String(100), nullable=False, index=True)  # 错误类型
    endpoint = Column(String(255), nullable=True, index=True)  # 发生错误的端点
    count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_error_metrics_date_type', 'metric_date', 'error_type', 'endpoint', unique=True),
    )