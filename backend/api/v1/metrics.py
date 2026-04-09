"""
监控指标 API
用于查看系统性能指标
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from pydantic import BaseModel

from auth.middleware import get_current_active_user, require_admin_role
from models import User, IntentClassificationLog, IntentMetrics, ErrorMetrics
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
    days: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    获取 AI 意图识别统计（仅管理员）

    Args:
        days: 查询最近几天的数据（与start_date/end_date互斥）
        start_date: 开始日期（自定义范围）
        end_date: 结束日期（自定义范围）
    """
    if start_date and end_date:
        # 自定义日期范围
        delta_days = (end_date - start_date).days + 1
        return metrics.get_intent_stats(delta_days)
    elif days:
        return metrics.get_intent_stats(days)
    else:
        # 默认近7天
        return metrics.get_intent_stats(7)


@router.get("/intent/trend")
async def get_intent_trend(
    days: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
) -> Dict[str, Any]:
    """
    获取 AI 意图识别每日趋势（用于折线图）

    Args:
        days: 查询最近几天的数据（与start_date/end_date互斥）
        start_date: 开始日期（自定义范围）
        end_date: 结束日期（自定义范围）
    """
    from sqlalchemy import func as sql_func

    # 计算日期范围
    if start_date and end_date:
        query_start_date = start_date
        query_end_date = end_date
        period_days = (end_date - start_date).days + 1
    elif days:
        query_start_date = date.today() - timedelta(days=days)
        query_end_date = date.today()
        period_days = days
    else:
        # 默认近7天
        query_start_date = date.today() - timedelta(days=7)
        query_end_date = date.today()
        period_days = 7

    # 查询每日各意图的识别次数
    daily_stats = db.query(
        IntentMetrics.metric_date,
        IntentMetrics.intent,
        IntentMetrics.total
    ).filter(
        IntentMetrics.metric_date >= query_start_date,
        IntentMetrics.metric_date <= query_end_date
    ).order_by(IntentMetrics.metric_date, IntentMetrics.intent).all()

    # 构建趋势数据
    dates = []
    current_date = query_start_date
    while current_date <= query_end_date:
        dates.append(current_date.isoformat())
        current_date += timedelta(days=1)

    # 按意图类型分组
    intent_types = list(set([stat.intent for stat in daily_stats]))

    # 构建每日数据
    trend_data = []
    for d in dates:
        day_data = {"date": d}
        for intent in intent_types:
            # 查找该日期该意图的数据
            stat = next(
                (s for s in daily_stats if s.metric_date.isoformat() == d and s.intent == intent),
                None
            )
            day_data[intent] = stat.total if stat else 0
        trend_data.append(day_data)

    return {
        "period_days": period_days,
        "dates": dates,
        "intents": intent_types,
        "data": trend_data
    }


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
    days: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
) -> Dict[str, int]:
    """
    获取错误统计（仅管理员）

    Args:
        days: 查询最近几天的数据（与start_date/end_date互斥）
        start_date: 开始日期（自定义范围）
        end_date: 结束日期（自定义范围）
    """
    from sqlalchemy import func as sql_func

    # 计算日期范围
    if start_date and end_date:
        query_start_date = start_date
        query_end_date = end_date
    elif days:
        query_start_date = date.today() - timedelta(days=days)
        query_end_date = date.today()
    else:
        # 默认近7天
        query_start_date = date.today() - timedelta(days=7)
        query_end_date = date.today()

    # 从数据库查询错误统计
    results = db.query(
        ErrorMetrics.error_type,
        ErrorMetrics.endpoint,
        sql_func.sum(ErrorMetrics.count).label('total')
    ).filter(
        ErrorMetrics.metric_date >= query_start_date,
        ErrorMetrics.metric_date <= query_end_date
    ).group_by(ErrorMetrics.error_type, ErrorMetrics.endpoint).all()

    errors = {}
    for r in results:
        key = f"{r.error_type}:{r.endpoint}" if r.endpoint else r.error_type
        errors[key] = r.total

    return errors


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
    days: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    随机抽取意图识别记录用于人工标注（仅管理员）

    Args:
        days: 查询最近几天的数据（与start_date/end_date互斥）
        start_date: 开始日期（自定义范围）
        end_date: 结束日期（自定义范围）
        limit: 抽取数量，默认10条
    """
    from sqlalchemy import func

    # 计算日期范围
    if start_date and end_date:
        query_start_date = start_date
        query_end_date = end_date
    elif days:
        query_start_date = date.today() - timedelta(days=days)
        query_end_date = date.today()
    else:
        # 默认近7天
        query_start_date = date.today() - timedelta(days=7)
        query_end_date = date.today()

    # 查询未抽样的记录，随机排序
    logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= query_start_date,
        IntentClassificationLog.metric_date <= query_end_date,
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
    days: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    获取抽样标注统计（仅管理员）

    Args:
        days: 查询最近几天的数据（与start_date/end_date互斥）
        start_date: 开始日期（自定义范围）
        end_date: 结束日期（自定义范围）
    """
    from sqlalchemy import func as sql_func, case

    # 计算日期范围
    if start_date and end_date:
        query_start_date = start_date
        query_end_date = end_date
        period_days = (end_date - start_date).days + 1
    elif days:
        query_start_date = date.today() - timedelta(days=days)
        query_end_date = date.today()
        period_days = days
    else:
        # 默认近7天
        query_start_date = date.today() - timedelta(days=7)
        query_end_date = date.today()
        period_days = 7

    # 总体统计
    total_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= query_start_date,
        IntentClassificationLog.metric_date <= query_end_date
    ).count()

    sampled_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= query_start_date,
        IntentClassificationLog.metric_date <= query_end_date,
        IntentClassificationLog.is_sampled == True
    ).count()

    annotated_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= query_start_date,
        IntentClassificationLog.metric_date <= query_end_date,
        IntentClassificationLog.is_correct != None
    ).count()

    correct_logs = db.query(IntentClassificationLog).filter(
        IntentClassificationLog.metric_date >= query_start_date,
        IntentClassificationLog.metric_date <= query_end_date,
        IntentClassificationLog.is_correct == True
    ).count()

    # 按意图统计
    intent_stats = db.query(
        IntentClassificationLog.intent,
        sql_func.count(IntentClassificationLog.id).label('total'),
        sql_func.sum(case((IntentClassificationLog.is_correct == True, 1), else_=0)).label('correct')
    ).filter(
        IntentClassificationLog.metric_date >= query_start_date,
        IntentClassificationLog.metric_date <= query_end_date,
        IntentClassificationLog.is_correct != None
    ).group_by(IntentClassificationLog.intent).all()

    return {
        "period_days": period_days,
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