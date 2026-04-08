"""
仪表盘统计 API
提供管理中心所需的各项业务统计数据
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import timedelta
from typing import Dict, Any, List

from db.session import get_db
from auth.middleware import get_current_active_user, require_admin_role
from models import User, Ticket
from models.chat import ChatSession, AgentStatus
from utils.timezone import now

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取仪表盘核心统计数据
    """
    # 检查权限（仅管理员和客服可访问）
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    now_time = now()
    today_start = now_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. 工单统计
    # 待处理工单（open + pending 状态）
    pending_tickets = db.query(Ticket).filter(
        Ticket.status.in_(["open", "pending"])
    ).count()

    # 今日创建的工单
    today_tickets = db.query(Ticket).filter(
        Ticket.created_at >= today_start
    ).count()

    # 已解决工单（今日）
    today_resolved = db.query(Ticket).filter(
        Ticket.status == "resolved",
        Ticket.resolved_at >= today_start
    ).count()

    # 总解决工单数
    total_resolved = db.query(Ticket).filter(
        Ticket.status == "resolved"
    ).count()

    # 2. 在线客服数
    online_agents = db.query(AgentStatus).filter(
        AgentStatus.status == "online"
    ).count()

    # 3. 进行中的会话数
    active_sessions = db.query(ChatSession).filter(
        ChatSession.status == "connected"
    ).count()

    # 4. 等待中的会话数
    waiting_sessions = db.query(ChatSession).filter(
        ChatSession.status == "waiting"
    ).count()

    return {
        "tickets": {
            "pending": pending_tickets,
            "today": today_tickets,
            "today_resolved": today_resolved,
            "total_resolved": total_resolved
        },
        "agents": {
            "online": online_agents
        },
        "sessions": {
            "active": active_sessions,
            "waiting": waiting_sessions
        }
    }


@router.get("/ticket-trends")
async def get_ticket_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取工单趋势数据（最近N天）
    """
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    now_time = now()
    date_list = []
    created_list = []
    resolved_list = []

    for i in range(days - 1, -1, -1):
        date_obj = now_time - timedelta(days=i)
        day_start = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        date_str = day_start.strftime("%m-%d")
        date_list.append(date_str)

        # 该日创建的工单数
        created_count = db.query(Ticket).filter(
            Ticket.created_at >= day_start,
            Ticket.created_at < day_end
        ).count()
        created_list.append(created_count)

        # 该日解决的工单数
        resolved_count = db.query(Ticket).filter(
            Ticket.resolved_at >= day_start,
            Ticket.resolved_at < day_end
        ).count()
        resolved_list.append(resolved_count)

    return {
        "dates": date_list,
        "created": created_list,
        "resolved": resolved_list
    }


@router.get("/ticket-categories")
async def get_ticket_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    获取工单分类统计
    """
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 按分类统计工单数量
    category_stats = db.query(
        Ticket.category,
        func.count(Ticket.id).label("count")
    ).group_by(Ticket.category).all()

    # 分类名称映射
    category_names = {
        "technical": "技术问题",
        "billing": "账单问题",
        "account": "账户问题",
        "general": "一般咨询",
        "other": "其他"
    }

    result = []
    for category, count in category_stats:
        result.append({
            "category": category,
            "name": category_names.get(category, category),
            "count": count
        })

    return result


@router.get("/ticket-priority")
async def get_ticket_priority_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    获取工单优先级统计
    """
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 按优先级统计工单数量
    priority_stats = db.query(
        Ticket.priority,
        func.count(Ticket.id).label("count")
    ).group_by(Ticket.priority).all()

    # 优先级名称映射
    priority_names = {
        "low": "低",
        "normal": "普通",
        "high": "高",
        "urgent": "紧急"
    }

    # 优先级顺序
    priority_order = ["urgent", "high", "normal", "low"]

    result = []
    # 按优先级顺序输出
    for priority in priority_order:
        count = next((c for p, c in priority_stats if p == priority), 0)
        result.append({
            "priority": priority,
            "name": priority_names.get(priority, priority),
            "count": count
        })

    return result


@router.get("/agent-performance")
async def get_agent_performance(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
) -> List[Dict[str, Any]]:
    """
    获取客服绩效统计（仅管理员）
    """
    now_time = now()
    start_date = now_time - timedelta(days=days)

    # 查询所有客服
    agents = db.query(User).join(User.role).filter(
        User.role.has(code="agent")
    ).all()

    result = []
    for agent in agents:
        # 该客服处理的工单数
        handled_tickets = db.query(Ticket).filter(
            Ticket.assigned_agent_id == agent.id,
            Ticket.created_at >= start_date
        ).count()

        # 该客服解决的工单数
        resolved_tickets = db.query(Ticket).filter(
            Ticket.assigned_agent_id == agent.id,
            Ticket.status == "resolved",
            Ticket.resolved_at >= start_date
        ).count()

        # 当前状态
        agent_status = db.query(AgentStatus).filter(
            AgentStatus.agent_id == agent.id
        ).first()

        result.append({
            "id": agent.id,
            "name": agent.full_name or agent.username,
            "handled": handled_tickets,
            "resolved": resolved_tickets,
            "status": agent_status.status if agent_status else "offline"
        })

    # 按解决数排序
    result.sort(key=lambda x: x["resolved"], reverse=True)

    return result


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    获取最近活动（最近创建的工单）
    """
    if current_user.role.code not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 最近创建的工单
    recent_tickets = db.query(Ticket).order_by(
        desc(Ticket.created_at)
    ).limit(limit).all()

    activities = []
    for ticket in recent_tickets:
        activities.append({
            "type": "ticket_created",
            "ticket_id": ticket.id,
            "ticket_no": ticket.ticket_no,
            "title": ticket.title,
            "customer": ticket.customer.username if ticket.customer else "Unknown",
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None
        })

    return activities