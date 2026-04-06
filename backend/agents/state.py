"""
LangGraph 智能体状态定义
"""
from typing import Annotated, Sequence, TypedDict, Union

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """智能体状态"""
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], "对话消息历史"]

    # 输入文本
    input: Annotated[str, "用户输入文本"]

    # 意图分类
    intent: Annotated[str, "识别的意图: create_ticket, query_ticket, process_ticket, summary, general"]

    # 工单信息
    ticket_info: Annotated[dict, "工单相关信息"]

    # 客户信息
    customer_info: Annotated[dict, "客户相关信息"]

    # 用户画像（长期记忆）
    user_profile: Annotated[dict, "用户画像信息，包含历史工单、统计等"]

    # 知识库检索结果
    knowledge_results: Annotated[list, "从知识库检索的结果"]

    # 工具调用结果
    tool_results: Annotated[list, "工具调用结果"]

    # 当前状态
    current_state: Annotated[str, "当前处理状态"]

    # 错误信息
    error: Annotated[str, "错误信息"]

    # 响应
    response: Annotated[str, "最终响应"]