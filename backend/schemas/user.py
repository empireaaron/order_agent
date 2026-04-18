"""
用户 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class RoleBase(BaseModel):
    """角色基础模型"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = []


class RoleCreate(BaseModel):
    """创建角色请求"""
    name: str
    code: str
    description: Optional[str] = None
    permissions: List[str] = []


class Role(RoleBase):
    """角色响应模型"""
    pass


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: int
    is_active: bool = True
    is_verified: bool = False


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: bool = True
    is_verified: bool = False
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class User(UserBase):
    """用户响应模型"""
    id: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    role: Optional[RoleBase] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str
    role: str
    exp: datetime