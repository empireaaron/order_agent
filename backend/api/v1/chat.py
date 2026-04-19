"""
聊天 API 路由 - 调用智能体处理用户消息
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from auth.middleware import get_current_active_user, require_admin_role
from models import User
from agents.nodes import get_ticket_bot_graph
from agents.state import AgentState
from memory.short_term import get_short_term_memory
from memory.user_profile import user_profile_manager, UserProfileManager
from api.v1.auth import _check_rate_limit

logger = logging.getLogger(__name__)

class ChatMessageRequest(BaseModel):
    """AI 聊天消息请求"""
    model_config = ConfigDict(extra="ignore")
    message: str = Field(..., min_length=1, max_length=5000, description="用户输入的消息")


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
async def chat_with_agent(
    message: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    与智能客服对话

    请求体:
    {
        "message": "用户输入的消息"
    }

    响应:
    {
        "response": "智能体回复",
        "intent": "识别的意图",
        "ticket_info": {}  // 如果创建了工单
    }
    """
    if not _check_rate_limit(f"chat_agent:{current_user.id}", max_requests=30, window=60):
        raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")

    user_input = message.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 1. 加载用户长期记忆（用户画像）
    user_profile = user_profile_manager.get_user_profile(current_user.id, db)
    profile_prompt = UserProfileManager.build_profile_prompt(user_profile)
    if profile_prompt:
        logger.debug("用户画像:\n%s", profile_prompt)

    # 2. 加载短期记忆（对话历史）
    user_id = str(current_user.id)
    history_messages = get_short_term_memory().get_messages_as_lc(user_id, limit=10)
    logger.debug("用户 %s 历史对话: %s 条", user_id, len(history_messages))

    # 3. 构建初始状态，包含历史对话和用户画像
    initial_state: AgentState = {
        "messages": history_messages,
        "input": user_input,
        "intent": "",
        "ticket_info": {},
        "customer_info": {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "user_profile": user_profile,  # 用户画像（长期记忆）
        "knowledge_results": [],
        "tool_results": [],
        "current_state": "start",
        "error": "",
        "response": ""
    }

    try:
        # 3. 执行智能体图（在线程池中运行，避免阻塞事件循环）
        result = await asyncio.to_thread(get_ticket_bot_graph().invoke, initial_state)

        response_text = result.get("response", "处理完成")

        # 4. 保存对话到记忆（用户输入 + AI回复）
        get_short_term_memory().add_message(user_id, "human", user_input)
        get_short_term_memory().add_message(user_id, "ai", response_text)

        return {
            "response": response_text,
            "intent": result.get("intent", "general"),
            "ticket_info": result.get("ticket_info", {}),
            "error": result.get("error", "")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("智能体处理失败: %s", e)
        raise HTTPException(status_code=500, detail="智能体处理失败，请稍后重试")


@router.post("/clear-history")
def clear_chat_history(
    current_user: User = Depends(get_current_active_user)
):
    """清除当前用户的历史对话记录"""
    user_id = str(current_user.id)
    get_short_term_memory().clear_memory(user_id)
    return {"message": "历史对话已清除"}


@router.delete("/clear-history/{user_id}")
def clear_user_chat_history(
    user_id: str,
    current_user: User = Depends(require_admin_role)
):
    """管理员清除指定用户的历史对话记录"""
    get_short_term_memory().clear_memory(user_id)
    return {"message": f"用户 {user_id} 的历史对话已清除"}