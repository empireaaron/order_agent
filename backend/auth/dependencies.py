"""
依赖注入函数
"""
from fastapi import Depends, HTTPException, status

from db.session import get_db
from auth.middleware import get_current_active_user, ROLE_ADMIN, ROLE_AGENT, ROLE_OPERATOR
from models import User, Ticket, KnowledgeBase, Document


def get_db_session():
    """获取数据库会话"""
    return next(get_db())


async def get_current_user_dependency(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前用户（依赖注入版本）"""
    return current_user


async def require_admin_dependency(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求管理员权限（依赖注入版本）"""
    if current_user.role.code != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    return current_user


async def require_agent_dependency(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求客服或管理员权限（依赖注入版本）"""
    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    return current_user


async def get_ticket_by_id(
    ticket_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db_session)
) -> Ticket:
    """获取工单（权限检查）"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # 客服可以查看所有工单，普通用户只能查看自己的
    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )

    return ticket


async def get_knowledge_base_by_id(
    kb_id: str,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db_session)
) -> KnowledgeBase:
    """获取知识库（权限检查）"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )

    # 非创建者只能查看
    if kb.owner_id != current_user.id and current_user.role.code not in [ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    return kb