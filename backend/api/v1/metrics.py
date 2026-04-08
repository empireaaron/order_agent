"""
监控指标 API
用于查看系统性能指标
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from pydantic import BaseModel

from auth.middleware import get_current_active_user, require_admin_role
from models import User, IntentClassificationLog, IntentMetrics
from db.session import get_db
from sqlalchemy.orm import Session
from utils.metrics import metrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


class AnnotationRequest(BaseModel):
    log_id: str
    is_correct: bool


class SampleResponse(BaseModel):
    log_id: str
    intent: str
    user_input: Optional[str]
    confidence: float
    created_at: str


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


@router.get("/intent/sample", response_model=List[SampleResponse])
async def get_intent_sample(
    days: int = 7,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    随机抽取意图识别记录用于人工标注（仅管理员）

    Args:
        days: 查询最近几天的数据，默认7天
        limit: 抽取数量，默认10条
    """
    from sqlalchemy import func

    start_date = date.today() - timedelta(days=days)

    # 查询未抽样的记录，随机排序
    logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= start_date,
        IntentClassificationLog.is_sampled == False
    ).order_by(func.random()).limit(limit).all()

    # 标记为已抽样
    for log in logs:
        log.is_sampled = True

    db.commit()

    return [{
        "log_id": log.id,
        "intent": log.intent,
        "user_input": log.user_input,
        "confidence": log.confidence,
        "created_at": log.created_at.isoformat() if log.created_at else None
    } for log in logs]


@router.post("/intent/annotate")
async def annotate_intent_sample(
    request: AnnotationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    提交意图识别人工标注结果（仅管理员）
    """
    from sqlalchemy.sql import func as sql_func

    log = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.id == request.log_id
    ).first()

    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 更新日志的标注结果
    log.is_correct = request.is_correct
    log.annotated_by = current_user.id
    log.annotated_at = sql_func.now()

    # 更新聚合统计表中的抽样数据
    metric = db.query(IntentMetrics).filter(
        IntentMetrics.metric_date == log.metric_date,
        IntentMetrics.intent == log.intent
    ).first()

    if metric:
        metric.sampled += 1
        if request.is_correct:
            metric.sampled_correct += 1

    db.commit()

    return {
        "status": "ok",
        "log_id": request.log_id,
        "intent": log.intent,
        "is_correct": request.is_correct
    }


@router.get("/intent/sample-stats")
async def get_intent_sample_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    获取抽样标注统计（仅管理员）
    """
    from sqlalchemy import func as sql_func

    start_date = date.today() - timedelta(days=days)

    # 总体统计
    total_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= start_date
    ).count()

    sampled_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= start_date,
        IntentClassificationLog.is_sampled == True
    ).count()

    annotated_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= start_date,
        IntentClassificationLog.is_correct != None
    ).count()

    correct_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= start_date,
        IntentClassificationLog.is_correct == True
    ).count()

    # 按意图统计
    intent_stats = db.query(
        IntentClassificationLog.intent,
        sql_func.count(IntentClassificationLog.id).label('total'),
        sql_func.sum(sql_func.case([(IntentClassificationLog.is_correct == True, 1)], else_=0)).label('correct')
    ).filter(
        IntentClassificationLog.metric_date >= start_date,
        IntentClassificationLog.is_correct != None
    ).group_by(IntentClassificationLog.intent).all()

    return {
        "period_days": days,
        "total_logs": total_logs,
        "sampled": sampled_logs,
        "annotated": annotated_logs,
        "correct": correct_logs,
        "sampled_accuracy": round(correct_logs / annotated_logs, 4) if annotated_logs > 0 else 0,
        "by_intent": {
            stat.intent: {
                "annotated": stat.total,
                "correct": stat.correct or 0,
                "accuracy": round((stat.correct or 0) / stat.total, 4) if stat.total > 0 else 0
            }
            for stat in intent_stats
        }
    }