# 记忆存储模块

支持两种存储后端：内存和 Redis。

## 后端切换

### 自动检测（默认）

```python
from memory.short_term import short_term_memory

# 自动检测：如果 Redis 可用则使用 Redis，否则使用内存
# 由 backend="auto" 自动处理
```

### 强制指定后端

```python
from memory.short_term import ShortTermMemory

# 强制使用内存
memory = ShortTermMemory(backend="memory")

# 强制使用 Redis（Redis 不可用时抛异常）
memory = ShortTermMemory(backend="redis")
```

## 配置

### 环境变量

```env
# Redis 配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_ENABLED=false  # 设置为 true 启用 Redis
```

### Docker Compose

Redis 服务已添加到 `docker-compose.yml`：

```bash
# 启动所有服务（包括 Redis）
docker-compose up -d

# 仅启动 Redis
docker-compose up -d redis
```

## 安装依赖

```bash
pip install redis
```

## 使用方式

```python
from memory.short_term import short_term_memory

# 添加消息
short_term_memory.add_message(user_id="user_001", role="human", content="你好")
short_term_memory.add_message(user_id="user_001", role="ai", content="您好！有什么可以帮您的？")

# 获取消息
messages = short_term_memory.get_messages("user_001", limit=10)

# 转换为 LangChain 格式
lc_messages = short_term_memory.get_messages_as_lc("user_001")

# 查看后端类型
print(short_term_memory.get_backend())  # "memory" 或 "redis"
```

## 自动摘要

当消息数量超过 10 条时，自动生成摘要：
- 保留最近 6 条消息原文
- 早期消息压缩为摘要

## 过期策略

- 内存模式：30 分钟无活动自动清理
- Redis 模式：使用 Redis TTL，默认 30 分钟