#!/usr/bin/env python3
"""
测试短期记忆功能
"""
import sys
sys.path.insert(0, './backend')

from memory.short_term import short_term_memory

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
    for msg in lc_messages:
        print(f"  [{msg.type}] {msg.content[:40]}...")

    # 测试对话摘要
    summary = short_term_memory.get_conversation_summary(user_id)
    print(f"\n对话摘要:\n{summary}")

    # 清理测试数据
    short_term_memory.clear_memory(user_id)
    print("\n✅ 短期记忆测试通过")


if __name__ == "__main__":
    test_short_term_memory()