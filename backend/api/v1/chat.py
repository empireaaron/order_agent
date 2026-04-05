"""
聊天 API 路由 - 调用智能体处理用户消息
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from auth.middleware import get_current_active_user
from models import User
from agents.nodes import ticket_bot_graph
from agents.state import AgentState

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat_with_agent(
    message: dict,
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
    user_input = message.get("message", "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 构建初始状态
    initial_state: AgentState = {
        "messages": [],
        "input": user_input,
        "intent": "",
        "ticket_info": {},
        "customer_info": {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        },
        "knowledge_results": [],
        "tool_results": [],
        "current_state": "start",
        "error": "",
        "response": ""
    }

    try:
        # 执行智能体图
        result = ticket_bot_graph.invoke(initial_state)

        return {
            "response": result.get("response", "处理完成"),
            "intent": result.get("intent", "general"),
            "ticket_info": result.get("ticket_info", {}),
            "error": result.get("error", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能体处理失败: {str(e)}")


@router.post("/stream")
def chat_with_agent_stream(
    message: dict,
    current_user: User = Depends(get_current_active_user)
):
    """流式聊天接口（预留）"""
    pass