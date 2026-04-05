# 实时客服聊天系统实现指南

## 系统概述

实时客服聊天系统已实现以下功能：
- **AI 智能客服**：基于 LangGraph 的意图识别
- **人工客服转接**：客户可主动转人工，支持自动分配和排队
- **实时通信**：WebSocket 双端点（/ws 和 /ws/chat）
- **客服工作台**：在线/离线状态管理，会话分配
- **消息持久化**：聊天记录保存到 MySQL 数据库

---

## 系统架构

### 数据库模型

已创建以下数据表：
- `chat_sessions` - 会话信息
- `chat_messages` - 聊天记录
- `agent_status` - 客服在线状态

### WebSocket 端点

- `/ws` - 通用 WebSocket（系统通知）
- `/ws/chat` - 聊天 WebSocket（实时消息）

### API 接口

- `POST /api/v1/chat-service/sessions` - 创建聊天会话
- `GET /api/v1/chat-service/sessions` - 获取会话列表
- `GET /api/v1/chat-service/sessions/waiting` - 获取等待队列
- `POST /api/v1/chat-service/sessions/{id}/accept` - 接入会话
- `POST /api/v1/chat-service/sessions/{id}/close` - 关闭会话
- `POST /api/v1/chat-service/sessions/{id}/messages` - 发送消息
- `POST /api/v1/agent/online` - 客服上线
- `POST /api/v1/agent/offline` - 客服下线

---

## 数据库迁移

```bash
# 进入backend目录
cd backend

# 初始化数据库（包含聊天相关表）
python manage.py init-db

# 或手动执行SQL
cat database.sql | grep -A 100 "chat_sessions"
```

---

## 后端集成

### 模型注册

```python
# models/__init__.py
from models.chat import ChatSession, ChatMessage, AgentStatus

__all__ = [
    # ... 原有模型
    "ChatSession",
    "ChatMessage",
    "AgentStatus",
]
```

### 路由注册

```python
# api/v1/__init__.py
from api.v1 import chat_service

app.include_router(chat_service.router, prefix=settings.API_V1_PREFIX)
```

### WebSocket 端点

```python
# main.py
from websocket.chat import chat_ws_manager

@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: str = Query(None)):
    """聊天WebSocket端点"""
    # 验证 Token
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    from auth.jwt import decode_token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    await websocket.accept()
    await chat_ws_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            await chat_ws_manager.handle_message(user_id, data)
    except WebSocketDisconnect:
        chat_ws_manager.disconnect(user_id)
```

---

## 前端集成

### 路由配置

```typescript
// App.tsx
import ChatWorkplace from './pages/ChatWorkplace'

<Route path="/chat-workplace" element={<ChatWorkplace />} />
```

### 菜单配置

```typescript
// 在菜单配置中添加
{
  key: '/chat-workplace',
  icon: <CustomerServiceOutlined />,
  label: '客服工作台',
}
```

---

## Widget 转人工集成

### 转人工流程

1. 客户点击"转人工"按钮
2. 调用 API 创建会话
3. 根据返回状态：
   - `connected` - 直接接入客服
   - `waiting` - 显示排队位置
4. 建立 WebSocket 连接
5. 实时收发消息

### 关键代码

```javascript
async transferToHuman() {
  this.addMessage('正在为您转接人工客服，请稍候...', 'system');

  try {
    const response = await fetch(`${this.config.apiUrl}/chat-service/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.state.token}`
      },
      body: JSON.stringify({
        request_type: 'general',
        message: '客户请求转人工'
      })
    });

    const data = await response.json();

    if (data.status === 'connected') {
      this.addMessage(`客服 ${data.agent.name} 已为您服务`, 'system');
      this.state.chatSessionId = data.session_id;
      this.connectChatWebSocket(data.session_id);
    } else {
      this.addMessage(`当前排队位置：第${data.queue_position}位，请稍候...`, 'system');
      this.state.chatSessionId = data.session_id;
      // 轮询等待接入
      this.pollSessionStatus(data.session_id);
    }
  } catch (error) {
    this.addMessage('转接失败，请稍后重试', 'system');
  }
}

connectChatWebSocket(sessionId) {
  const ws = new WebSocket(`${this.config.websocketUrl}/ws/chat?token=${this.state.token}`);

  ws.onopen = () => {
    ws.send(JSON.stringify({
      type: 'join_session',
      session_id: sessionId,
      role: 'customer'
    }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'new_message') {
      this.addMessage(data.message.content, data.message.sender_type);
    }
  };

  this.state.chatWs = ws;
}
```

---

## 功能测试清单

### 客服端测试 ✅
- [x] 客服点击"上线"按钮，状态变为在线
- [x] 客户发起转人工，客服收到新会话提醒
- [x] 客服点击"接入"，可以与客户实时聊天
- [x] 客服可以发送和接收消息
- [x] 客服点击"结束会话"，会话关闭
- [x] 客服点击"下线"，不再接收新会话

### 客户端测试（Widget）✅
- [x] 客户点击"转人工"按钮
- [x] 如果客服在线，直接接入
- [x] 如果客服忙碌，显示排队位置
- [x] 客户可以实时接收客服消息
- [x] 客户可以发送消息给客服
- [x] 页面刷新后自动恢复会话

### 并发测试 ✅
- [x] 多个客户同时转人工，排队功能正常
- [x] 客服可以同时处理多个会话
- [x] 消息不串线，每个会话独立

---

## AI 智能客服与人工客服切换

### 触发转人工的方式

1. **关键词触发**：
   - "转人工"
   - "人工客服"
   - "人工服务"
   - "找客服"

2. **按钮触发**：
   - Widget 中的"转人工"按钮

3. **AI 判断**：
   - AI 无法回答时建议转人工
   - 客户情绪不佳时主动建议

### 转人工流程

```
用户输入
    ↓
AI 分析意图
    ↓
├─ 普通咨询 → 查询知识库 → 返回答案
├─ 工单相关 → 工单操作 → 返回结果
└─ 转人工 → 创建会话 → 自动分配/排队 → 建立连接
```

---

## 已知问题与解决方案

### 1. Token 认证问题
**问题**：401 Unauthorized 错误
**解决**：确保 token 正确存储在 localStorage 或 zustand persist 中，API 拦截器正确读取

### 2. WebSocket 连接问题
**问题**：WebSocket 连接失败
**解决**：确保 WebSocket 在 Token 验证后才 accept()

### 3. 会话恢复问题
**问题**：页面刷新后会话丢失
**解决**：Widget 使用 localStorage 保存会话 ID，重新连接时自动加入

---

## 后续优化建议

1. **消息持久化优化**
   - 使用 Redis 缓存最近消息
   - 数据库异步写入

2. **智能分配**
   - 根据客服技能标签分配
   - 负载均衡算法

3. **消息增强**
   - 图片/文件传输
   - 消息已读状态
   - 客服输入状态提示

4. **监控统计**
   - 客服在线时长
   - 平均响应时间
   - 客户满意度

5. **离线消息**
   - 客服离线时客户可以留言
   - 客服上线后推送未读消息

6. **AI 增强**
   - 客服辅助回复建议
   - 自动工单生成
   - 情感分析