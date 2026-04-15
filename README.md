# TicketBot - 智能客服工单系统

基于 FastAPI + LangChain + LangGraph 的智能客服工单系统，支持多角色权限管理、知识库检索、实时通信、人工客服转接、系统监控。

## 功能特性

### 权限管理
- JWT Token 认证，支持管理员、客服、运营、普通用户多角色
- 基于角色的访问控制（RBAC）

### 工单系统
- 创建、查询、处理工单
- 工单状态管理（待处理/处理中/已解决/已关闭/已取消）
- 工单消息和备注
- 客户对工单的操作（催促/取消/关闭/重新打开/补充信息）

### 实时客服系统
- **AI 智能客服**：基于 LangGraph 的意图识别和自动路由
- **人工客服**：支持转人工服务，自动分配或排队等待
- **WebSocket 实时通信**：客户与客服实时聊天
- **客服工作台**：在线/离线状态管理，会话分配

### 知识库
- 支持多知识库管理
- 文档上传（txt/pdf/docx/md/html）
- 基于向量检索的语义搜索
- Milvus 向量数据库存储

### 系统监控（管理员）
- **API 性能监控**：响应时间、P50/P95/P99 分位值、错误率
- **AI 意图识别监控**：识别次数、准确率、每日趋势
- **错误统计**：按类型和端点聚合
- **WebSocket 监控**：活跃连接数、消息量
- **抽样标注**：随机抽取意图识别日志进行人工标注，验证真实准确率

### 嵌入式 Widget
- Vanilla JS 实现，无依赖
- 可直接嵌入任何网站
- 支持登录状态持久化
- 自动重连和会话恢复

## 技术架构

### 后端
- **FastAPI**：高性能 API 框架
- **LangChain + LangGraph**：AI 智能体编排
- **MySQL**：主数据存储
- **Milvus**：向量数据库
- **WebSocket**：实时通信（双端点：/ws 和 /ws/chat）
- **MinIO**：文件存储
- **Redis**：可选，用于短期记忆存储

### 前端
- **React 18 + TypeScript**：管理后台
- **Ant Design**：UI 组件库
- **Zustand**：状态管理
- **TanStack Query**：数据获取
- **Recharts**：数据可视化

### 嵌入式组件
- **Vanilla JS**：无依赖，可直接嵌入
- **Shadow DOM**：样式隔离

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env 文件，填入你的配置
```

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

# Redis (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=false
```

### 2. 启动依赖服务

```bash
docker-compose up -d mysql milvus minio
```

### 3. 初始化数据库

```bash
python manage.py init-db
```

### 4. 启动后端

```bash
# 方式1：使用管理脚本（推荐）
python manage.py run-backend

# 方式2：直接使用 uvicorn
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

后端服务：
- API：http://localhost:8001
- API 文档：http://localhost:8001/docs

### 5. 启动前端

```bash
cd frontend-admin
npm install
npm run dev
```

前端服务：http://localhost:5173

### 6. 测试 Widget

打开 `widget/demo.html` 文件，或使用本地服务器：

```bash
cd widget
python -m http.server 8080
```

访问 http://localhost:8080/demo.html

## 项目结构

```
order_agent/
├── backend/                 # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置管理
│   ├── manage.py           # 管理脚本（已迁移到根目录）
│   ├── models/             # 数据模型
│   │   ├── user.py         # 用户、角色模型
│   │   ├── ticket.py       # 工单模型
│   │   ├── knowledge_base.py # 知识库模型
│   │   ├── chat.py         # 实时聊天模型
│   │   └── metrics.py      # 监控指标模型
│   ├── api/                # API 路由
│   │   ├── auth.py         # 认证接口
│   │   ├── tickets.py      # 工单接口
│   │   ├── knowledge.py    # 知识库接口
│   │   ├── chat_service.py # 实时聊天接口
│   │   └── metrics.py      # 监控指标接口
│   ├── agents/             # LangGraph 智能体
│   │   ├── nodes.py        # 节点函数（意图识别、知识库查询等）
│   │   └── state.py        # 状态定义
│   ├── auth/               # 权限认证
│   ├── memory/             # 短期记忆存储
│   │   ├── short_term.py   # 内存/Redis 双后端
│   │   └── README.md       # 使用文档
│   ├── middleware/         # FastAPI 中间件
│   │   └── metrics.py      # 监控指标中间件
│   ├── tools/              # 工具函数
│   │   ├── mysql_tools.py  # MySQL 工具
│   │   ├── milvus_tools.py # Milvus 工具
│   │   └── document_processor.py # 文档解析
│   ├── utils/              # 通用工具
│   │   └── metrics.py      # 监控指标收集器
│   └── websocket/          # WebSocket 管理
│       ├── manager.py      # 通用连接管理
│       └── chat.py         # 聊天连接管理
│
├── frontend-admin/         # React 管理后台
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   ├── ChatWorkplace/  # 客服工作台
│   │   │   ├── KnowledgeBase/  # 知识库管理
│   │   │   ├── Tickets/        # 工单管理
│   │   │   ├── Metrics.tsx     # 系统监控
│   │   │   └── SamplingAnnotation.tsx  # 抽样标注
│   │   ├── stores/         # Zustand 状态管理
│   │   └── services/       # API 服务
│   └── package.json
│
├── widget/                 # 嵌入式客服组件
│   ├── ticket-widget.js    # 核心组件
│   └── demo.html           # 演示页面
│
├── docker-compose.yml      # Docker 编排
├── manage.py               # 项目管理脚本
├── .vscode/                # VS Code 调试配置
└── README.md               # 本文件
```

## 开发指南

### 后端开发

```bash
cd backend

# 使用 VS Code 调试（推荐）
# 按 F5 选择 "Run Backend" 即可启动

# 或使用命令行
python manage.py run-backend
```

### 前端开发

```bash
cd frontend-admin
npm install
npm run dev
```

### 常用命令

```bash
# 初始化数据库
python manage.py init-db

# 启动后端
python manage.py run-backend

# 启动前端
python manage.py run-frontend
```

### 解决 Python 导入问题

如果遇到 `ModuleNotFoundError: No module named 'config'`，请确保：
1. backend 目录下有 `__init__.py` 文件
2. 设置了 `PYTHONPATH` 包含 backend 目录
3. 使用管理脚本运行

在 Claude Code 中，使用以下方式确保导入正确：

```python
import sys
sys.path.insert(0, './backend')
from config import settings
from models import User
```

## API 文档

启动服务后访问：http://localhost:8001/docs

### 主要接口

| 接口 | 说明 |
|------|------|
| `POST /api/v1/auth/login` | 用户登录 |
| `POST /api/v1/auth/register` | 用户注册 |
| `GET /api/v1/tickets/` | 工单列表 |
| `POST /api/v1/tickets/` | 创建工单 |
| `POST /api/v1/knowledge/search` | 知识库搜索 |
| `POST /api/v1/chat-service/sessions` | 创建聊天会话（转人工） |
| `GET /api/v1/metrics/` | 获取所有监控指标 |
| `GET /api/v1/metrics/intent` | 获取意图识别统计 |
| `GET /api/v1/metrics/api` | 获取 API 性能统计 |
| `WebSocket /ws/chat` | 实时聊天连接 |

## AI 智能体工作流

系统使用 LangGraph 构建智能对话流程：

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

## 实时客服流程

### 客户侧
1. 在 Widget 中点击"转人工"
2. 系统自动分配在线客服，或进入排队
3. 建立 WebSocket 连接，实时收发消息
4. 支持刷新页面后自动恢复会话

### 客服侧
1. 登录管理后台，进入"聊天工作台"
2. 点击"上线接单"切换为在线状态
3. 自动接收分配的客户会话
4. 可查看等待队列，手动接入

## 嵌入 Widget

在任意网站中嵌入客服组件：

```html
<script src="https://your-domain.com/widget/ticket-widget.js"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    TicketWidget.init({
      apiUrl: 'http://localhost:8001/api/v1',
      websocketUrl: 'ws://localhost:8001/ws',
      title: '在线客服',
      welcomeMessage: '您好！我是智能客服助手，有什么可以帮您的吗？',
      theme: 'blue',
      showBubble: true
    });
  });
</script>
```

## Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8001 | FastAPI 服务 |
| 前端开发 | 5173 | Vite 开发服务器 |
| Widget 演示 | 8080 | Python HTTP 服务器 |
| MySQL | 3306 | 数据库 |
| Milvus | 19530 | 向量数据库 |
| MinIO API | 9000 | 文件存储 API |
| MinIO Console | 9001 | 文件存储控制台 |
| Redis | 6379 | 可选，用于短期记忆 |

## 默认账号

系统初始化时会创建默认角色：
- **管理员**：可管理所有资源，查看系统监控
- **客服**：可处理工单和接入客户
- **运营**：可查看数据报表
- **普通用户**：可创建工单和使用客服

## 许可证

[MIT](LICENSE)