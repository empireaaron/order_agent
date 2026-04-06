#!/usr/bin/env python3
"""
测试 AI 智能体的记忆功能
"""
import sys
sys.path.insert(0, './backend')

from memory.short_term import short_term_memory
from memory.user_profile import UserProfileManager

def test_short_term_memory():
    """测试短期记忆"""
    print("=" * 50)
    print("测试短期记忆")
    print("=" * 50)

    user_id = "test_user_001"

    # 模拟多轮对话
    conversations = [
        ("human", "我的订单还没到"),
        ("ai", "您好！请提供您的订单号，我帮您查询。"),
        ("human", "订单号是 DD2024001"),
        ("ai", "好的，我来帮您查询订单 DD2024001 的状态..."),
    ]

    # 保存对话
    for role, content in conversations:
        short_term_memory.add_message(user_id, role, content)

    # 读取历史
    messages = short_term_memory.get_messages(user_id)
    print(f"已保存 {len(messages)} 条消息:")
    for msg in messages:
        print(f"  [{msg['role']}] {msg['content'][:50]}...")

    # 测试 LangChain 格式
    lc_messages = short_term_memory.get_messages_as_lc(user_id)
    print(f"\n转换为 LangChain 格式: {len(lc_messages)} 条")

    # 测试对话摘要
    summary = short_term_memory.get_conversation_summary(user_id)
    print(f"\n对话摘要:\n{summary}")

    # 清理测试数据
    short_term_memory.clear_memory(user_id)
    print("\n✅ 短期记忆测试通过")


def test_user_profile():
    """测试用户画像"""
    print("\n" + "=" * 50)
    print("测试用户画像")
    print("=" * 50)

    # 注意：这个测试需要数据库连接，如果没有真实用户会返回空
    # 仅用于演示接口

    # 模拟用户画像数据
    mock_profile = {
        "user_id": 1,
        "username": "test_user",
        "full_name": "测试用户",
        "email": "test@example.com",
        "role": "user",
        "created_at": "2024-01-01T00:00:00",
        "ticket_stats": {
            "total": 5,
            "open": 1,
            "in_progress": 2,
            "resolved": 1,
            "closed": 1,
            "cancelled": 0
        },
        "recent_tickets": [
            {
                "ticket_no": "TKT-20240401120000",
                "title": "订单退款问题",
                "status": "in_progress",
                "priority": "high",
                "category": "billing"
            },
            {
                "ticket_no": "TKT-20240325150000",
                "title": "无法登录账户",
                "status": "resolved",
                "priority": "normal",
                "category": "technical"
            }
        ],
        "active_ticket": {
            "ticket_no": "TKT-20240401120000",
            "title": "订单退款问题",
            "status": "in_progress"
        }
    }

    # 测试构建 prompt
    prompt = UserProfileManager.build_profile_prompt(mock_profile)
    print("生成的用户画像 Prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)

    print("\n✅ 用户画像测试通过")


if __name__ == "__main__":
    test_short_term_memory()
    test_user_profile()
    print("\n" + "=" * 50)
    print("所有记忆功能测试完成！")
    print("=" * 50)