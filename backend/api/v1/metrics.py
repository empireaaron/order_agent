"""
监控指标 API
用于查看系统性能指标
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional

from auth.middleware import get_current_active_user, require_admin_role
from models import User
from utils.metrics import metrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/")
async def get_all_metrics(
    current_user: User = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    获取所有监控指标（仅管理员）
    """
    return metrics.get_all_stats()


@router.get("/api")
async def get_api_metrics(
    endpoint: Optional[str] = None,
    time_window_minutes: int = 60,
    current_user: User = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    获取 API 响应时间统计（仅管理员）
    """
    return metrics.get_api_stats(endpoint, time_window_minutes)


@router.get("/intent")
async def get_intent_metrics(
    days: int = 7,
    current_user: User = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    获取 AI 意图识别统计（仅管理员）

    Args:
        days: 查询最近几天的数据，默认7天
    """
    return metrics.get_intent_stats(days)


@router.post("/intent/feedback")
async def submit_intent_feedback(
    intent: str,
    is_correct: bool,
    current_user: User = Depends(get_current_active_user)
):
    """
    提交意图识别反馈（用于计算准确率）
    """
    metrics.record_intent_classification(intent, is_correct=is_correct)
    return {"status": "ok"}


@router.get("/errors")
async def get_error_metrics(
    days: int = 7,
    current_user: User = Depends(require_admin_role)
) -> Dict[str, int]:
    """
    获取错误统计（仅管理员）

    Args:
        days: 查询最近几天的数据，默认7天
    """
    return metrics.get_error_stats(days)


@router.get("/websocket")
async def get_websocket_metrics(
    current_user: User = Depends(require_admin_role)
) -> Dict[str, Any]:
    """获取 WebSocket 统计（仅管理员）"""
    return metrics.get_ws_stats()


@router.post("/reset")
async def reset_metrics(
    current_user: User = Depends(require_admin_role)
):
    """重置所有指标（谨慎使用，仅管理员）"""
    metrics.reset()
    return {"status": "reset"}