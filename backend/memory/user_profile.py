"""
用户画像管理 - 查询用户历史信息和工单记录
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models import User, Ticket, TicketMessage
logger = logging.getLogger(__name__)


class UserProfileManager:
    """用户画像管理器 - 聚合用户信息、历史工单等"""

    @staticmethod
    def get_user_profile(user_id: str, db: Session) -> Dict[str, Any]:
        """
        获取用户完整画像

        Args:
            user_id: 用户ID
            db: 数据库会话（由调用方提供）

        Returns:
            用户画像字典
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}

            # 1. 基础信息
            profile = {
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "full_name": user.full_name,
                "role": user.role.name if user.role else "user",
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

            # 2. 工单统计（使用 SQL GROUP BY，避免加载全部工单到内存）
            from sqlalchemy import func, case
            stats_result = db.query(
                func.count(Ticket.id).label("total"),
                func.sum(case((Ticket.status == "open", 1), else_=0)).label("open"),
                func.sum(case((Ticket.status.in_(["in_progress", "pending"]), 1), else_=0)).label("in_progress"),
                func.sum(case((Ticket.status == "resolved", 1), else_=0)).label("resolved"),
                func.sum(case((Ticket.status == "closed", 1), else_=0)).label("closed"),
                func.sum(case((Ticket.status == "cancelled", 1), else_=0)).label("cancelled"),
            ).filter(Ticket.customer_id == user_id).first()

            profile["ticket_stats"] = {
                "total": stats_result.total or 0,
                "open": stats_result.open or 0,
                "in_progress": stats_result.in_progress or 0,
                "resolved": stats_result.resolved or 0,
                "closed": stats_result.closed or 0,
                "cancelled": stats_result.cancelled or 0,
            }

            # 3. 最近工单摘要（最近3个）
            recent_tickets = db.query(Ticket).filter(
                Ticket.customer_id == user_id
            ).order_by(Ticket.created_at.desc()).limit(3).all()

            profile["recent_tickets"] = [
                {
                    "ticket_no": t.ticket_no,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "category": t.category,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in recent_tickets
            ]

            # 4. 最近活跃工单（如果有）- 单独查询，避免加载全部工单
            latest_active = db.query(Ticket).filter(
                Ticket.customer_id == user_id,
                Ticket.status.in_(["open", "pending", "in_progress"])
            ).order_by(Ticket.created_at.desc()).first()

            if latest_active:
                profile["active_ticket"] = {
                    "ticket_no": latest_active.ticket_no,
                    "title": latest_active.title,
                    "status": latest_active.status,
                    "created_at": latest_active.created_at.isoformat() if latest_active.created_at else None,
                }

                # 获取该工单的最新消息
                recent_messages = db.query(TicketMessage).filter(
                    TicketMessage.ticket_id == latest_active.id
                ).order_by(TicketMessage.created_at.desc()).limit(2).all()

                if recent_messages:
                    profile["recent_ticket_messages"] = [
                        {
                            "sender_type": m.sender_type,
                            "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                            "created_at": m.created_at.isoformat() if m.created_at else None,
                        }
                        for m in reversed(recent_messages)
                    ]

            return profile

        except Exception as e:
            logger.error("获取用户画像失败: %s", e)
            return {}

    @staticmethod
    def build_profile_prompt(profile: Dict[str, Any]) -> str:
        """
        将用户画像构建为 prompt 文本

        Args:
            profile: 用户画像字典

        Returns:
            prompt 文本
        """
        if not profile:
            return ""

        lines = ["【用户信息】"]

        # 基础信息
        lines.append(f"用户: {profile.get('full_name') or profile.get('username')}")
        lines.append(f"角色: {profile.get('role', 'user')}")

        # 注册时间（简化显示）
        created_at = profile.get('created_at')
        if created_at:
            lines.append(f"注册时间: {created_at[:10]}")

        # 工单统计
        stats = profile.get('ticket_stats', {})
        if stats.get('total', 0) > 0:
            lines.append(f"\n工单统计: 共{stats['total']}个")
            if stats['open'] > 0:
                lines.append(f"  - 待处理: {stats['open']}个")
            if stats['in_progress'] > 0:
                lines.append(f"  - 处理中: {stats['in_progress']}个")

        # 最近工单
        recent_tickets = profile.get('recent_tickets', [])
        if recent_tickets:
            lines.append("\n最近工单:")
            for i, t in enumerate(recent_tickets, 1):
                status_map = {
                    "open": "待处理", "pending": "待回复",
                    "in_progress": "处理中", "resolved": "已解决",
                    "closed": "已关闭", "cancelled": "已取消"
                }
                status = status_map.get(t['status'], t['status'])
                lines.append(f"  {i}. {t['ticket_no']} - {t['title'][:30]}... ({status})")

        # 活跃工单提醒
        active_ticket = profile.get('active_ticket')
        if active_ticket:
            lines.append(f"\n注意: 用户有正在处理的工单 {active_ticket['ticket_no']}")

        return "\n".join(lines)

    @staticmethod
    def get_recent_ticket_context(user_id: str, db: Session) -> str:
        """
        获取用户最近工单的上下文（用于简短提示）

        Args:
            user_id: 用户ID
            db: 数据库会话（由调用方提供）

        Returns:
            上下文文本
        """
        try:
            # 查询最近一个有消息的工单
            recent_ticket = db.query(Ticket).filter(
                Ticket.customer_id == user_id
            ).order_by(Ticket.created_at.desc()).first()

            if not recent_ticket:
                return ""

            # 查询该工单的最近消息
            messages = db.query(TicketMessage).filter(
                TicketMessage.ticket_id == recent_ticket.id
            ).order_by(TicketMessage.created_at.desc()).limit(3).all()

            if not messages:
                return f"用户最近创建的工单: {recent_ticket.ticket_no} - {recent_ticket.title}"

            context_parts = [f"最近工单 {recent_ticket.ticket_no} 的对话:"]
            for m in reversed(messages):
                sender = "客服" if m.sender_type == "agent" else "用户"
                content = m.content[:80] + "..." if len(m.content) > 80 else m.content
                context_parts.append(f"  {sender}: {content}")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error("获取工单上下文失败: %s", e)
            return ""


# 全局实例
user_profile_manager = UserProfileManager()