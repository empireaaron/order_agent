"""
认证 API 路由
"""
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import settings
from db.session import get_db
from models import User, Role
from schemas.user import UserCreate, User as UserSchema, Token
from auth.jwt import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from auth.middleware import get_current_user, get_current_active_user
from utils.timezone import now

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 基于内存的简单限流存储（生产环境建议使用 Redis）
_rate_limit_store = defaultdict(list)


def _check_rate_limit(key: str, max_requests: int = 5, window: int = 60) -> bool:
    """检查是否超过限流阈值"""
    now_ts = time.time()
    window_start = now_ts - window
    _rate_limit_store[key] = [ts for ts in _rate_limit_store[key] if ts > window_start]
    if len(_rate_limit_store[key]) >= max_requests:
        return False
    _rate_limit_store[key].append(now_ts)
    return True


@router.post("/register", response_model=UserSchema)
def register(request: Request, user_create: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(f"register:{client_ip}", max_requests=5, window=60):
        raise HTTPException(status_code=429, detail="Too many registration attempts")

    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_create.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user_create.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 注册接口强制使用 customer 角色，禁止用户自选角色
    role = db.query(Role).filter(Role.code == "customer").first()
    if not role:
        role = Role(name="Customer", code="customer", description="普通客户")
        db.add(role)
        db.commit()
        db.refresh(role)

    # 创建用户
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name,
        phone=user_create.phone,
        role_id=role.id,
        password_hash=get_password_hash(user_create.password),
        is_active=True,
        is_verified=False
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(f"login:{client_ip}", max_requests=5, window=60):
        raise HTTPException(status_code=429, detail="Too many login attempts")

    db_user = db.query(User).filter(User.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    db_user.last_login_at = now()
    db.commit()

    # 创建 token
    access_token = create_access_token(data={"sub": db_user.id, "role": db_user.role.code})
    refresh_token = create_refresh_token(data={"sub": db_user.id})

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新 token"""
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # 校验用户是否存在且有效
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # 创建新的 access token（带上当前角色）
    access_token = create_access_token(data={"sub": user_id, "role": db_user.role.code})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return user