# CLAUDE.md

本文档为 Claude Code (claude.ai/code) 提供本代码库的工作指导。

## 架构概述

TicketBot 是一个智能客服工单系统，包含三个主要组件：

1. **后端** (`backend/`) - FastAPI + LangChain/LangGraph AI 智能体
2. **前端管理后台** (`frontend-admin/`) - React + TypeScript + Ant Design，供客服/管理员使用
3. **嵌入式组件** (`widget/`) - Vanilla JS 聊天挂件，供网站客户使用

### AI 智能体工作流 (LangGraph)

AI 智能体 (`backend/agents/`) 通过意图分析处理用户输入：

```
用户输入 → 分析意图 → 路由到：
  ├─ 创建工单 → MySQL 插入
  ├─ 查询工单 → MySQL 查询
  ├─ 处理工单 → 更新工单状态
  ├─ 转人工 → 创建聊天会话
  ├─ 统计摘要 → 统计数据查询
  └─ 一般咨询 → 查询知识库 (Milvus) → 返回结果
```

### 实时聊天系统

WebSocket 双端点设计：
- `/ws` - 系统通知广播
- `/ws/chat` - 客户与客服实时聊天

转人工流程：
1. 客户在挂件中点击"转人工"或 AI 路由到人工
2. API 创建聊天会话 (`backend/api/v1/chat_service.py`)
3. 如有在线客服：自动分配或进入排队队列
4. 建立 WebSocket 连接进行实时消息收发
5. 客服在"聊天工作台" (`frontend-admin/src/pages/ChatWorkplace/`) 处理会话

### 关键目录

- `backend/agents/` - LangGraph 节点和状态定义
- `backend/api/v1/` - REST API 路由
- `backend/models/` - SQLAlchemy 模型（用户、工单、知识库、聊天）
- `backend/websocket/` - WebSocket 管理器（通用 + 聊天）
- `frontend-admin/src/stores/` - Zustand 状态管理
- `frontend-admin/src/services/` - API 客户端
- `widget/ticket-widget.js` - 可嵌入挂件（约1000行，Shadow DOM 隔离样式）

## 常用命令

```bash
# 初始化数据库
python manage.py init-db

# 启动后端（manage.py 使用 8000 端口，直接使用 uvicorn 用 8001）
python manage.py run-backend
# 或：cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 启动前端（端口 5173）
python manage.py run-frontend
# 或：cd frontend-admin && npm run dev

# 前端代码检查
cd frontend-admin && npm run lint

# Docker 启动依赖服务（MySQL、Milvus、MinIO）
docker-compose up -d mysql milvus minio

# Docker 启动所有服务
docker-compose up -d
```

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8001 | API + WebSocket |
| 前端开发 | 5173 | Vite 开发服务器 |
| MySQL | 3306 | 主数据库 |
| Milvus | 19530 | 向量数据库，用于知识库语义搜索 |
| MinIO API | 9000 | 文件存储 |
| MinIO 控制台 | 9001 | 文件管理界面 |

## 核心概念

**多角色权限控制**：JWT Token 认证，角色包括管理员、客服、运营、普通用户。权限检查见 `backend/auth/dependencies.py` 中的 `require_role()`。

**知识库处理**：文档上传到 MinIO，解析分块后通过 OpenAI/DashScope 生成向量，存储在 Milvus 中用于语义检索。

**挂件会话持久化**：Widget 将 `session_id` 和 `token` 保存在 localStorage 中，页面刷新后自动重连恢复会话。

**客服状态管理**：客服通过 `POST /api/v1/agent/online` 切换在线/离线状态，只有在线客服才会被分配新会话。

## VS Code 调试

按 `F5` 选择 "Run Backend" 或 "Run Frontend" 启动调试。配置位于 `.vscode/launch.json`。

## Python 路径

后端代码使用 `PYTHONPATH=./backend`。`manage.py` 会自动添加此路径，VS Code 启动配置也已处理。