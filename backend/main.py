"""
主应用入口
"""
import os
import logging

from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from api.v1 import auth, tickets, knowledge, users, chat, chat_service
from websocket.manager import ws_manager
from websocket.chat import chat_ws_manager
from auth.jwt import decode_token

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        description="智能客服工单系统 API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 路由
    app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    app.include_router(tickets.router, prefix=settings.API_V1_PREFIX)
    app.include_router(knowledge.router, prefix=settings.API_V1_PREFIX)
    app.include_router(users.router, prefix=settings.API_V1_PREFIX)
    app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
    app.include_router(chat_service.router, prefix=settings.API_V1_PREFIX)

    # 静态文件服务
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-admin", "dist")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()


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
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket 连接端点
    连接时需要提供 JWT token 参数: ws://localhost:8000/ws?token=xxx
    """
    # 先验证 token，然后再接受连接
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    try:
        # 验证 token
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token payload")
            return

        # 验证通过后才接受连接
        await websocket.accept()

        # 建立连接
        await ws_manager.connect(websocket, user_id)
        await websocket.send_json({"type": "connected", "user_id": user_id})

        try:
            # 保持连接并处理消息
            while True:
                data = await websocket.receive_json()

                # 处理不同类型的消息
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
                    # 广播消息给该用户的其他连接
                    await ws_manager.send_personal_message(
                        user_id,
                        {"type": "echo", "data": data}
                    )

        except WebSocketDisconnect:
            ws_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            ws_manager.disconnect(user_id)

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")


@app.websocket("/ws/chat")
async def chat_websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """
    实时聊天 WebSocket 端点
    连接时需要提供 JWT token 参数: ws://localhost:8000/ws/chat?token=xxx
    """
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    try:
        # 验证 token
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token payload")
            return

        # 验证通过后才接受连接
        await websocket.accept()

        # 建立连接
        await chat_ws_manager.connect(websocket, user_id)
        await websocket.send_json({"type": "connected", "user_id": user_id})

        try:
            # 保持连接并处理消息
            while True:
                data = await websocket.receive_json()
                await chat_ws_manager.handle_message(user_id, data)

        except WebSocketDisconnect:
            chat_ws_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"Chat WebSocket error for user {user_id}: {e}")
            chat_ws_manager.disconnect(user_id)

    except Exception as e:
        logger.error(f"Chat WebSocket connection error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)