"""
权限中间件
"""
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from models import User
from db.session import get_db
from .jwt import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 公共角色代码
ROLE_ADMIN = "admin"
ROLE_AGENT = "agent"
ROLE_OPERATOR = "operator"


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
) -> User:
    """获取当前用户"""
    print(f"DEBUG: get_current_user called with token={token[:20] + '...' if token else 'None'}")
    payload = decode_token(token)
    print(f"DEBUG: decode_token result={payload}")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前激活用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


async def require_admin_role(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求管理员角色"""
    if current_user.role.code != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource",
        )
    return current_user


async def require_agent_or_admin_role(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求客服或管理员角色"""
    if current_user.role.code not in [ROLE_ADMIN, ROLE_AGENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource",
        )
    return current_user


async def require_operator_role(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求运营角色"""
    if current_user.role.code not in [ROLE_ADMIN, ROLE_OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource",
        )
    return current_user