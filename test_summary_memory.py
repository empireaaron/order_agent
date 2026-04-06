#!/usr/bin/env python3
"""
测试带自动摘要的短期记忆功能
"""
import sys
sys.path.insert(0, './backend')

from memory.short_term import short_term_memory

def test_summary_memory():
    """测试自动摘要功能"""
    print("=" * 60)
    print("测试 ConversationSummaryBufferMemory 功能")
    print("=" * 60)

    user_id = "test_user_001"

    # 模拟长对话（超过10条触发摘要）
    conversations = [
        ("human", "你好，我想了解一下退款政策"),
        ("ai", "您好！我们的退款政策是：在购买后30天内可以申请退款，需满足未使用条件。"),
        ("human", "那如果我已经使用了部分服务呢？"),
        ("ai", "如果已使用部分服务，我们会按比例扣除已使用部分的费用，剩余部分可以退款。"),
        ("human", "退款需要多久到账？"),
        ("ai", "退款申请审核通过后，将在3-5个工作日内原路退回您的支付账户。"),
        ("human", "我如何申请退款？"),
        ("ai", "您可以在个人中心-订单管理中找到对应订单，点击申请退款按钮，填写退款原因提交即可。"),
        ("human", "我的订单号是 TKT-001"),
        ("ai", "好的，我帮您查询一下订单 TKT-001 的状态..."),
        ("human", "查询结果如何？"),  # 第11条，应该触发摘要
        ("ai", "订单 TKT-001 状态为已完成，符合退款条件，您可以直接申请退款。"),
        ("human", "好的，我已经提交了申请"),
        ("ai", "收到！您的退款申请已提交，审核结果将在24小时内通知您。"),
    ]

    print(f"\n模拟 {len(conversations)} 轮对话...")
    print(f"配置: 触发摘要阈值={short_term_memory.summary_trigger}, 保留原文={short_term_memory.buffer_size}条\n")

    for i, (role, content) in enumerate(conversations, 1):
        short_term_memory.add_message(user_id, role, content)

        # 显示每轮后的状态
        stats = short_term_memory.get_stats(user_id)
        if i == short_term_memory.summary_trigger:
            print(f"第 {i} 轮: 触发摘要生成！")
            print(f"  当前消息数: {stats['total_messages']}")
            print(f"  是否有摘要: {stats['has_summary']}")

    print("\n" + "=" * 60)
    print("对话结束后记忆状态")
    print("=" * 60)

    # 获取统计
    stats = short_term_memory.get_stats(user_id)
    print(f"\n统计信息:")
    print(f"  总消息数: {stats['total_messages']}")
    print(f"  用户消息: {stats['human_messages']}")
    print(f"  AI消息: {stats['ai_messages']}")
    print(f"  是否有摘要: {stats['has_summary']}")
    print(f"  摘要长度: {stats['summary_length']} 字符")

    # 获取完整对话记录
    print(f"\n存储的消息:")
    messages = short_term_memory.get_messages(user_id)
    for i, msg in enumerate(messages, 1):
        role = msg['role']
        content = msg['content'][:60]
        is_summary = msg.get('is_summary', False)
        marker = "[摘要]" if is_summary else ""
        print(f"  {i}. {marker} {role}: {content}...")

    # 转换为 LangChain 格式
    print(f"\nLangChain 格式消息:")
    lc_messages = short_term_memory.get_messages_as_lc(user_id)
    for msg in lc_messages:
        print(f"  [{msg.type}] {msg.content[:60]}...")

    # 调试信息
    print("\n" + "=" * 60)
    print("完整对话摘要视图")
    print("=" * 60)
    summary_view = short_term_memory.get_conversation_summary(user_id)
    print(summary_view)

    # 清理测试数据
    short_term_memory.clear_memory(user_id)
    print("\n[OK] 测试完成，已清理测试数据")


if __name__ == "__main__":
    test_summary_memory()