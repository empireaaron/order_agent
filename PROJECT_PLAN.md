# 智能客服工单系统 - 项目方案

## 项目概述

构建一个完整的智能客服工单系统，包含：
1. **后端**：FastAPI + LangChain + LangGraph
2. **前端**：混合架构（管理后台 React + 嵌入式 Widget Vanilla JS）
3. **数据库**：MySQL + Milvus 向量数据库
4. **实时通信**：WebSocket 双端点（/ws 和 /ws/chat）
5. **权限**：JWT Token 认证（管理员/客服/运营/普通用户多角色）
6. **知识库**：支持多知识库，文档上传（txt/word/pdf/markdown/html）
7. **AI 智能客服**：基于 LangGraph 的意图识别和自动路由
8. **人工客服**：实时聊天、自动分配、排队等待

---

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI |
| AI框架 | LangChain + LangGraph |
| 前端 - 管理后台 | React 18 + TypeScript + Vite |
| 前端 - 嵌入式Widget | Vanilla JS + Shadow DOM |
| 主数据库 | MySQL 8.0 |
| 向量数据库 | Milvus |
| 实时通信 | WebSocket |
| 文件存储 | MinIO |
| 认证 | JWT Token |
| 文档处理 | python-docx / pypdf / markdown / beautifulsoup4 |

---

## 已实现功能

### 1. 权限管理
- [x] JWT Token 认证
- [x] 多角色支持（管理员、客服、运营、普通用户）
- [x] 基于角色的访问控制（RBAC）

### 2. 工单系统
- [x] 创建、查询、处理工单
- [x] 工单状态管理（待处理/处理中/已解决/已关闭/已取消）
- [x] 工单消息和备注
- [x] 客户对工单的操作（催促/取消/关闭/重新打开/补充信息）

### 3. 实时客服系统
- [x] **AI 智能客服**：基于 LangGraph 的意图识别
- [x] **人工客服**：支持转人工服务，自动分配或排队等待
- [x] **WebSocket 实时通信**：客户与客服实时聊天
- [x] **客服工作台**：在线/离线状态管理，会话分配
- [x] **消息持久化**：聊天记录保存到数据库

### 4. 知识库
- [x] 多知识库管理
- [x] 文档上传（txt/pdf/docx/md/html）
- [x] 基于向量检索的语义搜索
- [x] Milvus 向量数据库存储

### 5. 嵌入式 Widget
- [x] Vanilla JS 实现，无依赖
- [x] 可直接嵌入任何网站
- [x] 支持登录状态持久化
- [x] 自动重连和会话恢复
- [x] 支持转人工服务

---

## 后端项目结构

```
backend/
├── main.py                    # FastAPI 入口
├── config.py                  # 配置管理
├── manage.py                  # 管理脚本
├── requirements.txt           # Python 依赖
│
├── models/                    # 数据模型
│   ├── __init__.py
│   ├── user.py               # 用户、角色模型
│   ├── ticket.py             # 工单模型
│   ├── knowledge_base.py     # 知识库模型
│   └── chat.py               # 实时聊天模型
│
├── db/                        # 数据库相关
│   ├── __init__.py
│   ├── session.py            # MySQL 会话管理
│   └── milvus.py             # Milvus 连接
│
├── auth/                      # 认证模块
│   ├── __init__.py
│   ├── jwt.py                # JWT 生成/验证
│   ├── middleware.py         # 权限校验中间件
│   └── dependencies.py       # 依赖注入
│
├── agents/                    # LangGraph 智能体
│   ├── __init__.py
│   ├── graph.py              # StateGraph 定义
│   ├── nodes.py              # 各节点函数
│   └── state.py              # State 定义
│
├── tools/                     # 工具函数
│   ├── __init__.py
│   ├── mysql_tools.py        # MySQL 工具
│   ├── milvus_tools.py       # Milvus 工具
│   └── document_parser.py    # 文档解析
│
├── schemas/                   # Pydantic Schema
│   ├── __init__.py
│   ├── ticket.py
│   ├── user.py
│   ├── knowledge_base.py
│   └── chat.py               # 聊天相关 Schema
│
├── websocket/                 # WebSocket 管理
│   ├── __init__.py
│   ├── manager.py            # 通用连接管理
│   └── chat.py               # 聊天连接管理
│
└── api/                       # API 路由
    ├── __init__.py
    └── v1/
        ├── __init__.py
        ├── auth.py           # 认证接口
        ├── tickets.py        # 工单接口
        ├── knowledge.py      # 知识库接口
        ├── chat_service.py   # 实时聊天接口
        └── users.py          # 用户管理接口
```

---

## 前端项目结构

```
frontend-admin/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes/               # 路由配置
│   ├── pages/                # 页面组件
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Tickets/          # 工单管理
│   │   ├── KnowledgeBase/    # 知识库管理
│   │   ├── ChatWorkplace/    # 客服工作台
│   │   └── Users/            # 用户管理
│   ├── components/           # 公共组件
│   ├── hooks/                # 自定义 Hooks
│   ├── stores/               # Zustand 状态管理
│   ├── services/             # API 服务
│   └── lib/                  # 工具函数
└── package.json
```

---

## AI 智能体工作流

```
用户输入
    ↓
analyze_intent（意图分析）
    ↓
├─ create_ticket → 创建工单
├─ query_ticket → 查询工单
├─ process_ticket → 处理工单（催促/取消/关闭等）
├─ transfer_to_agent → 转人工客服
├─ summary → 统计摘要
└─ general → query_knowledge → 有结果？直接返回 : 通用回复
```

---

## 实时客服流程

### 客户侧
1. 在 Widget 中点击"转人工"或输入关键词
2. 系统自动分配在线客服，或进入排队
3. 建立 WebSocket 连接，实时收发消息
4. 支持刷新页面后自动恢复会话

### 客服侧
1. 登录管理后台，进入"聊天工作台"
2. 点击"上线接单"切换为在线状态
3. 自动接收分配的客户会话
4. 可查看等待队列，手动接入

---

## 部署结构

```
docker-compose.yml
└── services:
    ├── mysql:        # MySQL 8.0
    ├── milvus:       # Milvus Standalone
    └── minio:        # MinIO 文件存储
```

---

## API 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8001 | FastAPI 服务 |
| 前端开发 | 5173 | Vite 开发服务器 |
| MySQL | 3306 | 数据库 |
| Milvus | 19530 | 向量数据库 |
| MinIO | 9000/9001 | 文件存储 |

---

## 环境变量

主要配置项：
```env
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ticket_bot

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM (支持 OpenAI/DashScope)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen3.5-flash
EMBEDDING_MODEL=text-embedding-v2

# JWT
JWT_SECRET_KEY=your-secret-key

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```