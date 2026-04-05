"""
通用响应模型
"""
from typing import Generic, TypeVar, List, Optional

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    size: int = 10


class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    code: int = 200
    message: str = "success"
    data: List[T]
    meta: PaginationMeta


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int
    message: str
    detail: Optional[str] = None
    errors: Optional[List[dict]] = None


def create_response(data: T, message: str = "success", code: int = 200) -> ApiResponse[T]:
    """创建统一响应"""
    return ApiResponse(code=code, message=message, data=data)


def create_paginated_response(
    items: List[T],
    total: int,
    page: int = 1,
    size: int = 10
) -> PaginatedResponse[T]:
    """创建分页响应"""
    pages = (total + size - 1) // size if size > 0 else 1
    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
    )


def create_error_response(
    message: str,
    code: int = 500,
    detail: Optional[str] = None,
    errors: Optional[List[dict]] = None
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        code=code,
        message=message,
        detail=detail,
        errors=errors
    )