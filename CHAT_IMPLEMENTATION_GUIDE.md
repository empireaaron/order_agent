# 实时客服聊天系统实现指南

## 一、数据库迁移

```bash
# 1. 进入backend目录
cd backend

# 2. 创建迁移脚本（如果使用Alembic）
alembic revision --autogenerate -m "add_chat_session_models"

# 3. 执行迁移
alembic upgrade head

# 或者手动执行SQL
cat database.sql | grep -A 50 "chat_sessions"
```

## 二、后端集成

### 1. 更新 models/__init__.py
```python
from models.chat import ChatSession, ChatMessage, AgentStatus

__all__ = [
    # ... 原有模型
    "ChatSession",
    "ChatMessage",
    "AgentStatus",
]
```

### 2. 更新 api/v1/__init__.py
```python
from api.v1 import chat_service

app.include_router(chat_service.router, prefix=settings.API_V1_PREFIX)
```

### 3. 更新 main.py WebSocket路由
```python
from websocket.chat import chat_ws_manager

@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: str = Query(None)):
    """聊天WebSocket端点"""
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

## 三、前端集成

### 1. 创建页面路由
```typescript
// App.tsx
import ChatWorkplacePage from './pages/ChatWorkplacePage'

<Route path="chat-workplace" element={<ChatWorkplacePage />} />
```

### 2. 创建页面组件
```typescript
// pages/ChatWorkplacePage.tsx
import React from 'react'
import ChatWorkplace from '../components/ChatWorkplace'

const ChatWorkplacePage: React.FC = () => {
  return (
    <div>
      <h1>客服工作台</h1>
      <ChatWorkplace />
    </div>
  )
}

export default ChatWorkplacePage
```

### 3. 添加到菜单
```typescript
// layouts/MainLayout.tsx
{
  key: '/chat-workplace',
  icon: <CustomerServiceOutlined />,
  label: '客服工作台',
}
```

## 四、Widget转人工集成

### 1. 添加转人工按钮
```javascript
// 在widget-header中添加
<div class="ticket-widget-actions">
  <button id="tw-transfer-btn" class="ticket-widget-transfer">转人工</button>
</div>
```

### 2. 添加转人工逻辑
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

## 五、功能测试清单

### 1. 客服端测试
- [ ] 客服点击"上线"按钮，状态变为在线
- [ ] 客户发起转人工，客服收到新会话提醒
- [ ] 客服点击"接入"，可以与客户实时聊天
- [ ] 客服可以发送和接收消息
- [ ] 客服点击"结束会话"，会话关闭
- [ ] 客服点击"下线"，不再接收新会话

### 2. 客户端测试（Widget）
- [ ] 客户点击"转人工"按钮
- [ ] 如果客服在线，直接接入
- [ ] 如果客服忙碌，显示排队位置
- [ ] 客户可以实时接收客服消息
- [ ] 客户可以发送消息给客服

### 3. 并发测试
- [ ] 多个客户同时转人工，排队功能正常
- [ ] 客服可以同时处理多个会话
- [ ] 消息不串线，每个会话独立

## 六、后续优化建议

1. **消息持久化优化**
   - 使用Redis缓存最近消息
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