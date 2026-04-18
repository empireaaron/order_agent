"""
主应用入口
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose.exceptions import JOSEError

from config import settings
from api.v1 import auth, tickets, knowledge, users, chat, chat_service, metrics as metrics_api, dashboard
from websocket.manager import ws_manager
from websocket.chat import chat_ws_manager
from auth.jwt import decode_token
from middleware.metrics import MetricsMiddleware
from utils.metrics import metrics

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")
    # 清理指标收集器线程池
    try:
        metrics._executor.shutdown(wait=False)
    except Exception as e:
        logger.warning(f"Metrics executor shutdown error: {e}")
    # 清理 Milvus 连接
    try:
        from db.milvus import get_milvus_manager
        manager = get_milvus_manager()
        if manager and manager.client:
            manager.client.close()
            logger.info("Milvus connection closed")
    except Exception as e:
        logger.warning(f"Milvus shutdown error: {e}")
    # 清理文档处理线程池
    try:
        from api.v1.knowledge import _doc_processor_pool
        _doc_processor_pool.shutdown(wait=False)
        logger.info("Document processor pool shut down")
    except Exception as e:
        logger.warning(f"Doc processor pool shutdown error: {e}")
    # 清理 SQLAlchemy engine
    try:
        from db.session import engine
        engine.dispose()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.warning(f"Database engine shutdown error: {e}")
    # 清理 Redis 连接
    try:
        from memory.redis_store import redis_store
        if redis_store.is_available():
            redis_store.client.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Redis shutdown error: {e}")


def create_app():
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        description="智能客服工单系统 API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # 全局异常处理器 - 捕获所有未处理的异常
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "message": str(exc) if settings.DEBUG else "Something went wrong"
            }
        )

    # SQLAlchemy 数据库异常处理器
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Database error",
                "message": str(exc) if settings.DEBUG else "Database operation failed"
            }
        )

    # 请求验证错误处理器
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc}")
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors
            }
        )

    # CORS 中间件
    # 生产环境应通过 CORS_ORIGINS 环境变量限制具体域名
    # 例如: CORS_ORIGINS="https://admin.example.com,https://widget.example.com"
    cors_origins = settings.CORS_ORIGINS_LIST
    allow_creds = True
    if "*" in cors_origins:
        logger.warning(
            "CORS is configured to allow all origins (*). "
            "Disabling allow_credentials to prevent security risks. "
            "Please set CORS_ORIGINS to specific domains in production."
        )
        allow_creds = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_creds,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        max_age=600,
    )

    # 监控指标中间件
    app.add_middleware(MetricsMiddleware)

    # API 路由
    app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    app.include_router(tickets.router, prefix=settings.API_V1_PREFIX)
    app.include_router(knowledge.router, prefix=settings.API_V1_PREFIX)
    app.include_router(users.router, prefix=settings.API_V1_PREFIX)
    app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
    app.include_router(chat_service.router, prefix=settings.API_V1_PREFIX)
    app.include_router(metrics_api.router, prefix=settings.API_V1_PREFIX)
    app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)

    # 静态文件服务
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-admin", "dist")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()


async def authenticate_websocket(websocket: WebSocket) -> tuple[bool, str | None]:
    """
    验证 WebSocket 连接的 Token 和 Origin
    返回: (是否验证成功, 用户ID)
    """
    # Origin 校验：防止跨站 WebSocket 劫持
    origin = websocket.headers.get("origin")
    allowed_origins = settings.CORS_ORIGINS_LIST
    if "*" not in allowed_origins:
        if not origin or origin not in allowed_origins:
            logger.warning("WebSocket connection rejected: origin '%s' not allowed", origin)
            await websocket.close(code=4002, reason="Origin not allowed")
            return False, None

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4001, reason="Token required")
        return False, None

    try:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return False, None

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token payload")
            return False, None

        return True, user_id
    except (JOSEError, ValueError) as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return False, None


async def handle_websocket_connection(
    websocket: WebSocket,
    manager,
    user_id: str,
    message_handler=None
):
    """
    通用 WebSocket 连接处理
    manager: WebSocket 管理器实例
    message_handler: 可选的消息处理函数，接收 (user_id, data) 参数
    """
    await manager.connect(websocket, user_id)
    await websocket.send_json({"type": "connected", "user_id": user_id})

    try:
        while True:
            data = await websocket.receive_json()

            if message_handler:
                await message_handler(user_id, data)
            else:
                # 默认消息处理
                msg_type = data.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "subscribe_ticket":
                    ticket_id = data.get("ticket_id")
                    await websocket.send_json({
                        "type": "subscribed",
                        "ticket_id": ticket_id
                    })
                else:
                    await manager.send_personal_message(
                        user_id,
                        {"type": "echo", "data": data}
                    )

    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await manager.disconnect(user_id, websocket)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接端点
    连接时需要提供 JWT token 参数: ws://localhost:8000/ws?token=xxx
    """
    authenticated, user_id = await authenticate_websocket(websocket)
    if not authenticated:
        return

    await websocket.accept()
    await handle_websocket_connection(websocket, ws_manager, user_id)


@app.websocket("/ws/chat")
async def chat_websocket_endpoint(websocket: WebSocket):
    """
    实时聊天 WebSocket 端点
    连接时需要提供 JWT token 参数: ws://localhost:8000/ws/chat?token=xxx
    """
    authenticated, user_id = await authenticate_websocket(websocket)
    if not authenticated:
        return

    await websocket.accept()
    await handle_websocket_connection(
        websocket,
        chat_ws_manager,
        user_id,
        message_handler=chat_ws_manager.handle_message
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)