"""
监控指标中间件
自动收集 API 响应时间和错误统计
"""
import time
import logging
import re
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utils.metrics import metrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """自动收集 API 指标中间件"""

    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            endpoint = self._normalize_path(path)
            metrics.record_api_latency(
                endpoint=endpoint,
                method=request.method,
                latency_ms=latency_ms
            )

            if response.status_code >= 400:
                error_type = f"HTTP{response.status_code}"
                metrics.record_error(error_type, endpoint)

            response.headers["X-Response-Time-Ms"] = str(round(latency_ms, 2))
            return response

        except Exception as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            endpoint = self._normalize_path(path)
            metrics.record_api_latency(
                endpoint=endpoint,
                method=request.method,
                latency_ms=latency_ms
            )
            metrics.record_error(type(e).__name__, endpoint)
            logger.error(f"Request failed: {request.method} {path} - {e}")
            raise

    def _normalize_path(self, path: str) -> str:
        """规范化路径"""
        if path.startswith("/api/v1"):
            path = path[7:]

        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)

        return path