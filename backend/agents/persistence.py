"""
LangGraph 持久化配置（可选）

当前客服场景不需要图级别持久化，因为：
1. 每次 invoke 执行很快（< 1秒）
2. 对话历史已通过 ShortTermMemory 保存
3. 无断点恢复需求

如需实现，取消下面的注释并配置数据库连接。
"""
# from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.memory import MemorySaver

# 内存检查点（演示用，重启丢失）
# memory_checkpointer = MemorySaver()

# SQLite 检查点（持久化）
# sqlite_checkpointer = SqliteSaver.from_conn_string("checkpoints.sqlite")

# 使用方式：
# workflow.compile(checkpointer=memory_checkpointer)