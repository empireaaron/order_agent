# 智能客服工单系统 - 项目方案

## 项目概述

用户需要构建一个智能客服工单系统，用于面试演示。系统需包含：
1. 后端：FastAPI + LangChain + LangGraph
2. 前端：混合架构（管理后台 React + 嵌入式 Widget Vanilla JS）
3. 数据库：MySQL + Milvus 向量数据库
4. 通信：WebSocket 实时消息
5. 权限：JWT Token 认证（客服/运营/管理员角色）
6. 知识库：支持多知识库，文档上传（txt/word/pdf/markdown）

---

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI |
| AI框架 | LangChain + LangGraph |
| 前端 - 管理后台 | React 18 + TypeScript + Vite |
| 前端 - 嵌入式Widget | Vanilla JS + Web Components |
| 主数据库 | MySQL 8.0 (用户/工单/知识库元数据) |
| 向量数据库 | Milvus (知识库语义检索) |
| 实时通信 | WebSocket |
| 认证 | JWT Token |
| 文档处理 | python-docx / pypdf / markdown |

---

## 后端实现计划

### 项目结构

```
backend/
├── main.py                    # FastAPI 入口，注册路由
├── config.py                  # 配置管理 (MySQL/Milvus/LLM)
├── requirements.txt           # Python 依赖
├── database.sql               # MySQL 数据库初始化脚本
│
├── models/                    # 数据模型
│   ├── __init__.py
│   ├── user.py               # User, Role, Permission 模型
│   ├── ticket.py             # Ticket, TicketMessage 模型
│   └── knowledge_base.py     # KnowledgeBase, Document 模型
│
├── db/                        # 数据库相关
│   ├── __init__.py
│   ├── session.py            # MySQL 会话管理
│   └── milvus.py             # Milvus 连接和索引
│
├── auth/                      # 认证模块
│   ├── __init__.py
│   ├── jwt.py                # JWT 生成/验证
│   ├── middleware.py         # 权限校验中间件
│   └── dependencies.py       # 依赖注入（当前用户）
│
├── agents/                    # LangGraph 智能体
│   ├── __init__.py
│   ├── graph.py              # StateGraph 定义
│   ├── nodes.py              # 各节点函数
│   └── state.py              # StateTypedDict 定义
│
├── tools/                     # 工具函数
│   ├── __init__.py
│   ├── mysql_tools.py        # 工单 CRUD 工具
│   ├── milvus_tools.py       # 知识库检索工具
│   └── document_parser.py    # 文档解析工具
│
├── schemas/                   # Pydantic Schema
│   ├── __init__.py
│   ├── ticket.py
│   ├── user.py
│   └── knowledge_base.py
│
├── websocket/                 # WebSocket 相关
│   ├── __init__.py
│   └── manager.py            # 连接管理
│
└── api/                       # API 路由
    ├── __init__.py
    ├── v1/
    │   ├── __init__.py
    │   ├── auth.py           # 认证接口
    │   ├── tickets.py        # 工单接口
    │   ├── knowledge.py      # 知识库接口
    │   └── users.py          # 用户管理接口
    └── dependencies.py
```

---

## 前端实现计划

### 管理后台 (React + TypeScript)

```tsx
# 使用的技术栈
- React 18 + TypeScript
- Vite (构建工具)
- Tailwind CSS + shadcn/ui
- React Router v6
- TanStack Query (数据获取)
- Zustand (状态管理)
```

**页面结构**：
```
frontend-admin/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes/               # 路由配置
│   ├── pages/                # 页面组件
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── TicketList.tsx
│   │   ├── TicketDetail.tsx
│   │   ├── KnowledgeBaseList.tsx
│   │   ├── KnowledgeEdit.tsx
│   │   └── UserList.tsx
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── contexts/
└── package.json
```

### 嵌入式 Widget (Vanilla JS)

```javascript
# ticket-widget.js (约 10KB)
- Web Component (自定义元素)
- Shadow DOM (样式隔离)
- localStorage (存储 JWT)
- fetch API (调用后端)
- WebSocket (实时消息)
```

---

## 部署结构

```
docker-compose.yml
└── services:
    ├── app:          # FastAPI 后端
    ├── mysql:        # MySQL 8.0
    ├── milvus:       # Milvus Standalone
    └── frontend:     # Nginx 前端
```