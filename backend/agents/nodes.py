"""
LangGraph 智能体节点函数
"""
import logging
from datetime import datetime
import re

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from config import settings
from db.session import get_db_context
from models import User, Ticket
from agents.state import AgentState
from utils.metrics import metrics

logger = logging.getLogger(__name__)


def analyze_intent(state: AgentState) -> AgentState:
    """意图分析节点"""
    messages = state["messages"]
    user_input = state["input"]

    # 构建意图分类 prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个工单系统的智能路由助手。请分析用户输入，判断其意图类别：

意图类别：
- create_ticket: 用户想要创建新的工单或报告问题
- query_ticket: 用户想要查询工单状态或历史
- process_ticket: 用户想要处理或解决工单问题
- summary: 用户想要获取统计数据或报表
- general: 一般性咨询或闲聊

请只返回意图类别，不要返回其他内容。""")
        , ("human", "{input}")
    ])

    chain = prompt | settings.llm
    response = chain.invoke({"input": user_input})

    intent = response.content.strip().lower()
    valid_intents = ["create_ticket", "query_ticket", "process_ticket", "summary", "general"]

    # 记录意图识别（准确率稍后通过用户反馈更新）
    final_intent = intent if intent in valid_intents else "general"
    metrics.record_intent_classification(final_intent)

    return {
        **state,
        "intent": final_intent
    }


def create_ticket_node(state: AgentState) -> AgentState:
    """创建工单节点 - 实际写入数据库"""
    user_input = state["input"]
    customer_info = state.get("customer_info", {})
    customer_id = customer_info.get("user_id")

    if not customer_id:
        return {
            **state,
            "response": "请先登录后再创建工单。",
            "error": "未登录"
        }

    try:
        with get_db_context() as db:
            # 从数据库获取用户信息
            customer = db.query(User).filter(User.id == customer_id).first()
            if not customer:
                return {
                    **state,
                    "response": "用户不存在，请重新登录。",
                    "error": "用户不存在"
                }

            # 使用 LLM 分析工单内容，提取标题和优先级
            prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个工单分析助手。请从用户输入中提取：
1. 工单标题（简短概括，不超过50字）
2. 优先级（low/normal/high/urgent）
3. 分类（technical/billing/account/general/other）

请以 JSON 格式返回：
{{"title": "...", "priority": "...", "category": "..."}}"""),
                ("human", "{input}")
            ])

            chain = prompt | settings.llm
            response = chain.invoke({"input": user_input})

            # 解析 LLM 响应
            try:
                import json
                result = json.loads(response.content)
                title = result.get("title") or user_input[:50]
                priority = result.get("priority") or "normal"
                category = result.get("category") or "general"
            except (json.JSONDecodeError, AttributeError, TypeError):
                title = user_input[:50] if len(user_input) > 50 else user_input
                priority = "normal"
                category = "general"

            # 创建工单到数据库
            from tools.mysql_tools import create_ticket
            ticket = create_ticket(
                db=db,
                title=title,
                content=user_input,
                customer_id=customer_id,
                priority=priority,
                category=category,
                customer_info={
                    "username": customer.username,
                    "email": customer.email,
                    "phone": customer.phone
                }
            )

            # 调试日志
            logger.debug(f"Created ticket: id={ticket.id}, priority={ticket.priority}, category={ticket.category}")

            return {
                **state,
                "ticket_info": {
                    "id": str(ticket.id),
                    "ticket_no": str(ticket.ticket_no),
                    "title": str(ticket.title) if ticket.title else title,
                    "priority": str(ticket.priority) if ticket.priority else priority,
                    "category": str(ticket.category) if ticket.category else category,
                    "status": str(ticket.status) if ticket.status else "open",
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None
                },
                "response": f"✅ 工单创建成功！\n\n工单编号：{ticket.ticket_no}\n标题：{ticket.title}\n优先级：{ticket.priority}\n分类：{ticket.category}\n\n我们将尽快处理您的问题，您可以通过工单编号查询处理进度。"
            }
    except Exception as e:
        return {
            **state,
            "response": f"创建工单失败：{str(e)}",
            "error": str(e)
        }


def query_ticket_node(state: AgentState) -> AgentState:
    """查询工单节点 - 实际查询数据库"""
    user_input = state["input"]
    customer_info = state.get("customer_info", {})
    customer_id = customer_info.get("user_id")

    # 解析工单号
    ticket_match = re.search(r'(TKT-\d{14}|\d{14})', user_input)
    ticket_no = ticket_match.group(1) if ticket_match else None

    # 检测是否查询所有工单
    all_keywords = ['所有', '全部', '列表', '多个', '几个', '多少']
    is_query_all = any(kw in user_input for kw in all_keywords)

    try:
        with get_db_context() as db:
            # 格式化状态映射
            status_map = {
                "open": "待处理",
                "pending": "待回复",
                "in_progress": "处理中",
                "resolved": "已解决",
                "closed": "已关闭"
            }

            # 如果有工单号，查询单个工单
            if ticket_no:
                ticket = db.query(Ticket).filter(Ticket.ticket_no == ticket_no).first()
                if not ticket:
                    return {
                        **state,
                        "response": f"未找到工单 {ticket_no}。请检查工单编号是否正确。"
                    }

                from models import TicketMessage
                message_count = db.query(TicketMessage).filter(
                    TicketMessage.ticket_id == ticket.id
                ).count()

                priority_map = {"low": "低", "normal": "普通", "high": "高", "urgent": "紧急"}

                response_text = f"""📋 工单详情

工单编号：{ticket.ticket_no}
标题：{ticket.title}
状态：{status_map.get(ticket.status, ticket.status)}
优先级：{priority_map.get(ticket.priority, ticket.priority)}
分类：{ticket.category}
创建时间：{ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else '-'}
消息数：{message_count}

{ticket.content[:200]}{'...' if len(ticket.content) > 200 else ''}
"""

                return {
                    **state,
                    "ticket_info": {
                        "id": str(ticket.id),
                        "ticket_no": str(ticket.ticket_no),
                        "title": str(ticket.title),
                        "priority": str(ticket.priority) if ticket.priority else "normal",
                        "category": str(ticket.category) if ticket.category else "general",
                        "status": str(ticket.status),
                        "query_result": "success"
                    },
                    "response": response_text
                }

            # 查询所有工单或最新工单
            if not customer_id:
                return {
                    **state,
                    "response": "请先登录后查询工单。"
                }

            # 查询该用户的所有工单
            tickets = db.query(Ticket).filter(
                Ticket.customer_id == customer_id
            ).order_by(Ticket.created_at.desc()).all()

            if not tickets:
                return {
                    **state,
                    "response": "您还没有创建任何工单。发送您遇到的问题，我可以帮您创建工单。"
                }

            # 如果只查询最新一个（不是查询所有）
            if not is_query_all:
                ticket = tickets[0]
                from models import TicketMessage
                message_count = db.query(TicketMessage).filter(
                    TicketMessage.ticket_id == ticket.id
                ).count()

                priority_map = {"low": "低", "normal": "普通", "high": "高", "urgent": "紧急"}

                response_text = f"""📋 最新工单详情

工单编号：{ticket.ticket_no}
标题：{ticket.title}
状态：{status_map.get(ticket.status, ticket.status)}
优先级：{priority_map.get(ticket.priority, ticket.priority)}
分类：{ticket.category}
创建时间：{ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else '-'}
消息数：{message_count}

{ticket.content[:200]}{'...' if len(ticket.content) > 200 else ''}

💡 提示：您共有 {len(tickets)} 个工单，如需查看所有工单，请说"查询我的所有工单"
"""

                return {
                    **state,
                    "ticket_info": {
                        "id": str(ticket.id),
                        "ticket_no": str(ticket.ticket_no),
                        "title": str(ticket.title),
                        "priority": str(ticket.priority) if ticket.priority else "normal",
                        "category": str(ticket.category) if ticket.category else "general",
                        "status": str(ticket.status),
                        "query_result": "success"
                    },
                    "response": response_text
                }

            # 查询所有工单列表
            total = len(tickets)
            status_count = {}
            for t in tickets:
                status_count[t.status] = status_count.get(t.status, 0) + 1

            status_lines = [f"{status_map.get(s, s)}: {c}" for s, c in status_count.items()]

            # 显示前10个工单
            ticket_list = []
            for i, t in enumerate(tickets[:10], 1):
                ticket_list.append(
                    f"{i}. {t.ticket_no} | {t.title[:25]}{'...' if len(t.title) > 25 else ''} | {status_map.get(t.status, t.status)}"
                )

            more_text = f"\n... 还有 {total - 10} 个工单" if total > 10 else ""

            response_text = f"""📋 您的所有工单（共 {total} 个）

状态分布：{" | ".join(status_lines)}

工单列表：
{"\n".join(ticket_list)}{more_text}

💡 提示：如需查看某个工单的详细信息，请提供工单编号（如 {tickets[0].ticket_no}）
"""

            return {
                **state,
                "ticket_info": {
                    "ticket_count": total,
                    "query_result": "list"
                },
                "response": response_text
            }

    except Exception as e:
        return {
            **state,
            "response": f"查询工单失败：{str(e)}",
            "error": str(e)
        }


def query_knowledge_node(state: AgentState) -> AgentState:
    """查询知识库节点 - 仅查询知识库，不创建工单，支持多轮对话记忆"""
    user_input = state["input"]
    customer_info = state.get("customer_info", {})
    messages = state.get("messages", [])

    # 构建对话历史上下文（限制长度，防止超出LLM上下文）
    conversation_history = ""
    MAX_HISTORY_LENGTH = 1500  # 历史消息最大长度
    if messages:
        history_parts = []
        current_length = 0
        # 最近3轮对话（6条消息），从旧到新
        for msg in messages[-6:]:
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "用户" if msg.type == "human" else "AI"
                content = msg.content
                # 单条消息截断
                if len(content) > 300:
                    content = content[:300] + "...[截断]"
                msg_text = f"{role}: {content}"
                # 检查总长度
                if current_length + len(msg_text) > MAX_HISTORY_LENGTH:
                    break
                history_parts.append(msg_text)
                current_length += len(msg_text) + 1  # +1 for newline
        if history_parts:
            conversation_history = "\n".join(history_parts)
            logger.debug(f"Conversation history: {len(conversation_history)} chars")

    try:
        with get_db_context() as db:
            # 1. 查询知识库
            from models import KnowledgeBase
            customer_id = customer_info.get("user_id")
            kb_context = ""
            kb_search_info = {"searched": False, "kb_count": 0, "results_count": 0}

            # 查询所有活跃的知识库（知识库全局共享，不需要登录）
            kb_list = db.query(KnowledgeBase).filter(
                KnowledgeBase.status == "active"
            ).all()

            kb_search_info["searched"] = True
            kb_search_info["kb_count"] = len(kb_list)
            logger.debug(f"Found {len(kb_list)} knowledge bases")

            if kb_list:
                # 2. 从知识库中检索相关内容（带相似度过滤）
                # 优化：预计算 embedding + 并行查询
                from tools.milvus_tools import generate_embedding, search_kb_batch

                # 2.1 只生成一次 embedding
                query_vector = generate_embedding(user_input)

                # 2.2 并行搜索所有知识库
                all_raw_results = search_kb_batch(
                    query_vector=query_vector,
                    knowledge_bases=kb_list,
                    top_k=10,
                    similarity_threshold=0.3
                )
                logger.debug(f"Knowledge base search returned {len(all_raw_results)} results")
                for x in all_raw_results:
                    '''打印搜素到的内容'''
                    logger.debug(f"-------------------------------------")
                    logger.debug(f"KB: {x.get('kb_name', 'unknown')} | Similarity: {x.get('similarity', 0)} | Content: {x.get('metadata', {}).get('content', '')}")
                # 3. 全局排序：按相似度降序排列
                if all_raw_results:
                    all_raw_results = sorted(
                        all_raw_results,
                        key=lambda x: x.get('similarity', 0),
                        reverse=True
                    )

                    # 只取前 8 条最相关的结果
                    top_results = all_raw_results[:8]
                    kb_search_info["results_count"] = len(top_results)

                    # 提取内容并拼接（限制长度，与历史消息一起不超过LLM上下文）
                    context_parts = []
                    total_length = 0
                    MAX_TOTAL_LENGTH = 3000  # 知识库内容最大长度（与MAX_HISTORY_LENGTH合计约4500字符）

                    for r in top_results:
                        content = r.get("metadata", {}).get("content", "")
                        similarity = r.get('similarity', 0)
                        kb_name = r.get('kb_name', 'unknown')

                        if content:
                            # 检查是否超出长度限制
                            if total_length + len(content) > MAX_TOTAL_LENGTH:
                                # 截断最后一条
                                remaining = MAX_TOTAL_LENGTH - total_length
                                if remaining > 100:  # 至少保留 100 字符才有意义
                                    content = content[:remaining] + "...[截断]"
                                else:
                                    break

                            context_parts.append(content)
                            total_length += len(content)

                    if context_parts:
                        kb_context = "\n\n".join(context_parts)
                        logger.debug(f"KB query success: {len(context_parts)} results, {total_length} chars")
                    else:
                        logger.debug("KB query completed with no valid content")

            # 3. 使用 LLM 生成回答
            if kb_context:
                # 构建精简的系统提示词（节省token）
                if conversation_history:
                    system_prompt = f"""你是客服助手。请根据知识库和历史回答。

历史：
{conversation_history}

知识库：
{kb_context}

无相关信息请建议创建工单。"""
                else:
                    system_prompt = f"""你是客服助手。请根据知识库回答。

知识库：
{kb_context}

无相关信息请建议创建工单。"""

                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", user_input)
                ])
                chain = prompt | settings.llm
                response = chain.invoke({})

                return {
                    **state,
                    "knowledge_results": [kb_context],
                    "response": response.content
                }
            else:
                # 没有知识库或没有匹配结果，使用通用回复
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """你是一个专业的客服助手。用户提出了一个问题，但没有匹配到知识库内容。
请：
1. 简要回应用户的问题
2. 建议用户创建工单以便人工客服详细处理
3. 告知用户可以提供更详细的信息以获得更好帮助"""),
                    ("human", "{input}")
                ])

                chain = prompt | settings.llm
                response = chain.invoke({"input": user_input})

                return {
                    **state,
                    "knowledge_results": [],
                    "response": response.content + "\n\n💡 提示：如需进一步帮助，您可以回复「创建工单」来提交问题给人工客服。"
                }

    except Exception as e:
        logger.error(f"Knowledge base query failed: {e}", exc_info=True)
        return {
            **state,
            "knowledge_results": [],  # 异常时设置为空列表
            "response": f"处理您的问题时出错：{str(e)}。建议创建工单以便人工处理。",
            "error": str(e)
        }


def process_ticket_node(state: AgentState) -> AgentState:
    """处理工单节点 - 处理工单相关操作（催促、取消、关闭、补充信息、重新打开）"""
    user_input = state["input"]
    customer_info = state.get("customer_info", {})
    customer_id = customer_info.get("user_id")

    if not customer_id:
        return {
            **state,
            "response": "请先登录后再操作工单。"
        }

    try:
        with get_db_context() as db:
            # 1. 使用 LLM 分析操作意图和提取工单号
            prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个工单操作分析助手。请分析用户输入，提取以下信息：

1. 操作类型 (operation):
   - urge: 催促处理工单
   - cancel: 取消工单
   - close: 关闭/确认解决工单
   - reopen: 重新打开已关闭工单
   - append: 补充信息/添加备注
   - unknown: 无法识别的操作

2. 工单号 (ticket_no): 提取用户提到的工单号（如 TKT-20240101120000 或 20240101120000），如果没有则返回 null

请以 JSON 格式返回：
{{"operation": "操作类型", "ticket_no": "工单号或null", "reason": "操作原因或补充内容"}}"""),
                ("human", "{input}")
            ])

            chain = prompt | settings.llm
            response = chain.invoke({"input": user_input})

            # 解析 LLM 响应
            try:
                import json
                result = json.loads(response.content)
                operation = result.get("operation", "unknown")
                ticket_no = result.get("ticket_no")
                reason = result.get("reason", user_input)
            except (json.JSONDecodeError, AttributeError, TypeError):
                # 如果 JSON 解析失败，使用简单规则匹配
                operation = _detect_operation_simple(user_input)
                ticket_no = _extract_ticket_no(user_input)
                reason = user_input

            logger.debug(f"Ticket operation analysis: operation={operation}")

            # 2. 如果没有工单号，查询用户的最新工单
            if not ticket_no:
                latest_ticket = db.query(Ticket).filter(
                    Ticket.customer_id == customer_id
                ).order_by(Ticket.created_at.desc()).first()

                if not latest_ticket:
                    return {
                        **state,
                        "response": "您还没有创建任何工单。如需创建工单，请描述您遇到的问题。"
                    }

                ticket_no = latest_ticket.ticket_no

            # 3. 查询工单
            ticket = db.query(Ticket).filter(
                Ticket.ticket_no == ticket_no,
                Ticket.customer_id == customer_id
            ).first()

            if not ticket:
                return {
                    **state,
                    "response": f"未找到工单 {ticket_no}。请检查工单编号是否正确，或该工单不属于您。"
                }

            # 4. 根据操作类型执行不同处理
            from models import TicketMessage

            if operation == "cancel":
                # 取消工单
                if ticket.status in ["closed", "resolved"]:
                    return {
                        **state,
                        "response": f"工单 {ticket_no} 已处于 {ticket.status} 状态，无法取消。"
                    }

                old_status = ticket.status
                ticket.status = "cancelled"
                db.commit()

                # 添加系统消息
                message = TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=customer_id,
                    sender_type="customer",
                    content=f"【客户取消工单】{reason}",
                )
                db.add(message)
                db.commit()

                return {
                    **state,
                    "response": f"✅ 工单 {ticket_no} 已成功取消。如有需要，您可以创建新的工单。"
                }

            elif operation == "close":
                # 关闭/确认解决工单
                if ticket.status in ["closed", "resolved"]:
                    return {
                        **state,
                        "response": f"工单 {ticket_no} 已经处于 {ticket.status} 状态，无需重复关闭。"
                    }

                ticket.status = "resolved"
                ticket.resolved_at = datetime.utcnow()
                db.commit()

                # 添加确认消息
                message = TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=customer_id,
                    sender_type="customer",
                    content=f"【客户确认解决】{reason}"
                )
                db.add(message)
                db.commit()

                return {
                    **state,
                    "response": f"✅ 工单 {ticket_no} 已标记为已解决。感谢您的反馈！"
                }

            elif operation == "reopen":
                # 重新打开工单
                if ticket.status not in ["closed", "resolved", "cancelled"]:
                    return {
                        **state,
                        "response": f"工单 {ticket_no} 当前状态为 {ticket.status}，无需重新打开。"
                    }

                old_status = ticket.status
                ticket.status = "reopened"
                db.commit()

                # 添加重新打开消息
                message = TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=customer_id,
                    sender_type="customer",
                    content=f"【客户重新打开工单】{reason}"
                )
                db.add(message)
                db.commit()

                return {
                    **state,
                    "response": f"✅ 工单 {ticket_no} 已重新打开，客服会尽快处理您的新问题。"
                }

            elif operation == "append":
                # 补充信息
                message = TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=customer_id,
                    sender_type="customer",
                    content=f"【客户补充信息】{reason}"
                )
                db.add(message)
                db.commit()

                return {
                    **state,
                    "response": f"✅ 已为工单 {ticket_no} 添加补充信息。客服会看到您的更新。"
                }

            elif operation == "urge":
                # 催促工单
                if ticket.status in ["closed", "resolved", "cancelled"]:
                    return {
                        **state,
                        "response": f"工单 {ticket_no} 已经{ticket.status}，无法催促处理。"
                    }

                # 添加催促消息
                message = TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=customer_id,
                    sender_type="customer",
                    content=f"【客户催促】请尽快处理此工单。原因：{reason}"
                )
                db.add(message)

                # 更新工单优先级为高
                if ticket.priority in ["low", "normal"]:
                    ticket.priority = "high"

                ticket.updated_at = datetime.utcnow()
                db.commit()

                status_map = {
                    "open": "待处理",
                    "pending": "待回复",
                    "in_progress": "处理中",
                    "resolved": "已解决",
                    "closed": "已关闭"
                }

                return {
                    **state,
                    "response": f"📢 已催促处理工单 {ticket_no}\n\n当前状态：{status_map.get(ticket.status, ticket.status)}\n优先级：已提升为高优先级\n\n客服会优先处理您的工单，请耐心等待。"
                }

            else:
                # 未知操作，提供通用回复
                return {
                    **state,
                    "response": f"您可以对工单 {ticket_no} 进行以下操作：\n• 催促处理 - 提升优先级\n• 补充信息 - 添加备注\n• 取消工单 - 取消未完成的工单\n• 确认解决 - 关闭已解决的工单\n• 重新打开 - 重新处理已关闭的工单\n\n请告诉我您想做什么？"
                }

    except Exception as e:
        logger.error(f"Ticket processing failed: {e}", exc_info=True)
        return {
            **state,
            "response": f"处理工单时出错：{str(e)}。请稍后重试或联系人工客服。",
            "error": str(e)
        }


def _detect_operation_simple(user_input: str) -> str:
    """简单规则匹配操作类型"""
    input_lower = user_input.lower()

    # 取消工单
    if any(kw in input_lower for kw in ["取消", "不要了", "作废", "撤销"]):
        return "cancel"

    # 关闭/确认解决
    if any(kw in input_lower for kw in ["关闭", "解决", "好了", "完成", "确认"]):
        return "close"

    # 重新打开
    if any(kw in input_lower for kw in ["重新打开", "重新处理", "还有问题", "没解决"]):
        return "reopen"

    # 催促
    if any(kw in input_lower for kw in ["催促", "快点", "急", "什么时候", "怎么还没"]):
        return "urge"

    # 补充信息
    if any(kw in input_lower for kw in ["补充", "补充信息", "补充说明", "还有"]):
        return "append"

    return "unknown"


def _extract_ticket_no(user_input: str) -> str:
    """从用户输入中提取工单号"""
    import re
    match = re.search(r'(TKT-\d{14}|\d{14})', user_input)
    return match.group(1) if match else None


def summary_node(state: AgentState) -> AgentState:
    """统计摘要节点 - 查询用户工单统计"""
    customer_info = state.get("customer_info", {})
    customer_id = customer_info.get("user_id")

    if not customer_id:
        return {
            **state,
            "response": "请先登录后查看统计信息。"
        }

    try:
        with get_db_context() as db:
            from models import Ticket
            from sqlalchemy import func

            # 统计各状态工单数量
            stats = db.query(Ticket.status, func.count(Ticket.id)).filter(
                Ticket.customer_id == customer_id
            ).group_by(Ticket.status).all()

            total = sum(count for _, count in stats)

            if total == 0:
                return {
                    **state,
                    "response": "您还没有创建任何工单。发送您遇到的问题，我可以帮您创建工单。"
                }

            status_map = {
                "open": "待处理",
                "pending": "待回复",
                "in_progress": "处理中",
                "resolved": "已解决",
                "closed": "已关闭"
            }

            stats_lines = [f"{status_map.get(s, s)}: {c}" for s, c in stats]

            # 查询最近工单
            recent_tickets = db.query(Ticket).filter(
                Ticket.customer_id == customer_id
            ).order_by(Ticket.created_at.desc()).limit(3).all()

            recent_text = "\n".join([
                f"• {t.ticket_no}: {t.title[:30]}{'...' if len(t.title) > 30 else ''} ({status_map.get(t.status, t.status)})"
                for t in recent_tickets
            ])

            response = f"""📊 您的工单统计

总工单数: {total}
{" | ".join(stats_lines)}

最近工单:
{recent_text}

如需查看详细内容，请提供工单编号。"""

            return {
                **state,
                "response": response
            }
    except Exception as e:
        return {
            **state,
            "response": f"查询统计信息失败：{str(e)}",
            "error": str(e)
        }


def general_node(state: AgentState) -> AgentState:
    """通用回答节点 - 智能对话回复，支持多轮对话记忆和用户画像"""
    user_input = state["input"]
    messages = state.get("messages", [])
    user_profile = state.get("user_profile", {})

    # 构建对话历史文本
    conversation_history = ""
    if messages:
        history_parts = []
        for msg in messages[-6:]:  # 最近6条消息
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "用户" if msg.type == "human" else "AI"
                history_parts.append(f"{role}: {msg.content}")
        if history_parts:
            conversation_history = "\n".join(history_parts)

    # 构建用户画像提示
    profile_prompt = ""
    if user_profile:
        stats = user_profile.get('ticket_stats', {})
        total = stats.get('total', 0)
        open_count = stats.get('open', 0) + stats.get('in_progress', 0)

        profile_parts = []
        profile_parts.append(f"用户: {user_profile.get('full_name') or user_profile.get('username')}")
        if total > 0:
            profile_parts.append(f"历史工单: {total}个")
        if open_count > 0:
            profile_parts.append(f"当前有{open_count}个处理中的工单")

        # 最近工单提醒
        recent_tickets = user_profile.get('recent_tickets', [])
        if recent_tickets:
            latest = recent_tickets[0]
            profile_parts.append(f"最近工单: {latest['ticket_no']} - {latest['title']}")

        if profile_parts:
            profile_prompt = "\n".join(profile_parts)

    # 使用 LLM 生成友好回复，带上历史上下文和用户画像
    if conversation_history:
        # 构建完整的 system prompt，包含用户画像
        system_content = """你是一个友好的客服助手。请根据对话历史、用户画像和用户的最新输入，提供有帮助的回复。"""

        if profile_prompt:
            system_content += f"\n\n【用户画像】\n{profile_prompt}"

        system_content += """\n\n【对话历史】
{history}

你可以帮助用户：
1. 创建工单 - 当用户描述问题或故障时
2. 查询工单 - 当用户提供工单号或询问工单状态时
3. 查看统计 - 当用户想了解工单概况时

请用友好、专业的语气回复，注意保持对话的连贯性。如果用户有正在处理的工单，可以主动询问是否需要跟进。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            ("human", "{input}")
        ])
        try:
            chain = prompt | settings.llm
            response = chain.invoke({"input": user_input, "history": conversation_history})
        except Exception as e:
            response = type('obj', (object,), {'content': f"您好！有什么可以帮您的吗？（历史对话加载失败）"})()
    else:
        # 没有历史对话，使用简化prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个友好的客服助手。

你可以帮助用户：
1. 创建工单 - 当用户描述问题或故障时
2. 查询工单 - 当用户提供工单号或询问工单状态时
3. 查看统计 - 当用户想了解工单概况时

请用友好、专业的语气回复。"""),
            ("human", "{input}")
        ])
        try:
            chain = prompt | settings.llm
            response = chain.invoke({"input": user_input})
        except Exception as e:
            return {
                **state,
                "response": f"您好！我是您的智能客服助手。\n\n我可以帮您：\n• 📋 创建新工单 - 描述您遇到的问题\n• 🔍 查询工单 - 提供工单编号查询进度\n• 📊 查看统计 - 了解您的工单概况\n\n请问有什么可以帮您的吗？"
            }

    return {
        **state,
        "response": response.content
    }


def route_intent(state: AgentState) -> str:
    """意图路由函数"""
    intent = state.get("intent", "general")
    routing_map = {
        "create_ticket": "create_ticket",
        "query_ticket": "query_ticket",
        "process_ticket": "process_ticket",
        "summary": "summary",
    }
    return routing_map.get(intent, "general")


def route_knowledge(state: AgentState) -> str:
    """知识库查询结果路由"""
    knowledge_results = state.get("knowledge_results", [])
    if knowledge_results and len(knowledge_results) > 0:
        # 有知识库结果，直接结束
        return "has_result"
    else:
        # 无知识库结果，走通用回复
        return "no_result"


# 构建工单处理图
def build_ticket_bot_graph():
    """构建工单处理图"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("analyze_intent", analyze_intent)
    workflow.add_node("create_ticket", create_ticket_node)
    workflow.add_node("query_ticket", query_ticket_node)
    workflow.add_node("process_ticket", process_ticket_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("query_knowledge", query_knowledge_node)
    workflow.add_node("general", general_node)

    # 设置入口点
    workflow.set_entry_point("analyze_intent")

    # 添加路由
    workflow.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {
            "create_ticket": "create_ticket",
            "query_ticket": "query_ticket",
            "process_ticket": "process_ticket",
            "summary": "summary",
            "general": "query_knowledge",  # general 意图先查询知识库
        }
    )

    # 知识库查询结果路由
    workflow.add_conditional_edges(
        "query_knowledge",
        route_knowledge,
        {
            "has_result": END,  # 有结果直接返回
            "no_result": "general",  # 无结果走通用回复
        }
    )

    # 设置出口
    for node in ["create_ticket", "query_ticket", "process_ticket", "summary", "general"]:
        workflow.add_edge(node, END)

    return workflow.compile()


# 全局图实例
ticket_bot_graph = build_ticket_bot_graph()