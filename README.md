# 🎫 TicketBot - 智能客服工单系统

基于 FastAPI + LangChain + LangGraph 的智能客服工单系统，支持多角色权限管理、知识库检索、WebSocket 实时通信。

## ✨ 功能特性

- **🔐 权限管理**：JWT Token 认证，支持管理员、客服、运营、普通用户多角色
- **📝 工单系统**：创建、查询、处理工单，支持多轮对话
- **🤖 AI 智能体**：基于 LangGraph 的意图识别和自动路由
- **📚 知识库**：支持多知识库管理，文档上传（txt/pdf/docx/md）
- **🔍 向量检索**：Milvus 向量数据库，语义搜索
- **💬 WebSocket**：工单状态实时推送
- **🌐 嵌入式 Widget**：可嵌入任何网站的客服组件

## 🏗️ 技术架构

### 后端
- **FastAPI**：高性能 API 框架
- **LangChain + LangGraph**：AI 智能体编排
- **MySQL**：主数据存储
- **Milvus**：向量数据库
- **WebSocket**：实时通信

### 前端
- **React 18 + TypeScript**：管理后台
- **Ant Design**：UI 组件库
- **Zustand**：状态管理
- **TanStack Query**：数据获取

### 嵌入式组件
- **Vanilla JS**：无依赖，可直接嵌入
- **Web Components**：样式隔离

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/ticketbot.git
cd ticketbot
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env 文件，填入你的配置
```

### 3. 使用 Docker Compose 启动

```bash
docker-compose up -d
```

服务将启动在：
- 前端：http://localhost
- 后端 API：http://localhost:8001
- API 文档：http://localhost:8001/docs

### 4. 初始化数据库

```bash
# 进入 MySQL 容器
docker-compose exec mysql mysql -uroot -p

# 执行数据库初始化脚本
source /docker-entrypoint-initdb.d/database.sql
```

## 📁 项目结构

```
ticketbot/
├── backend/                 # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置管理
│   ├── models/             # 数据模型
│   ├── api/                # API 路由
│   ├── agents/             # LangGraph 智能体
│   ├── auth/               # 权限认证
│   ├── tools/              # 工具函数
│   └── websocket/          # WebSocket 管理
│
├── frontend-admin/         # React 管理后台
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── stores/         # 状态管理
│   │   └── services/       # API 服务
│   └── package.json
│
├── widget/                 # 嵌入式客服组件
│   ├── ticket-widget.js    # 核心组件
│   └── demo.html           # 演示页面
│
├── docker-compose.yml      # Docker 编排
└── README.md
```

## 💻 开发指南

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload
```

### 前端开发

```bash
cd frontend-admin

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 🔌 API 文档

启动服务后访问：http://localhost:8001/docs

### 主要接口

| 接口 | 说明 |
|------|------|
| `POST /api/v1/auth/login` | 用户登录 |
| `POST /api/v1/auth/register` | 用户注册 |
| `GET /api/v1/auth/me` | 获取当前用户 |
| `GET /api/v1/tickets/` | 工单列表 |
| `POST /api/v1/tickets/` | 创建工单 |
| `GET /api/v1/tickets/{id}` | 工单详情 |
| `POST /api/v1/knowledge/` | 创建知识库 |
| `POST /api/v1/knowledge/search` | 知识库搜索 |

## 🌐 嵌入 Widget

在任意网站中嵌入客服组件：

```html
<script src="https://your-domain.com/ticket-widget.js" defer></script>
<script>
  TicketWidget.init({
    apiUrl: 'https://api.your-domain.com',
    websocketUrl: 'wss://api.your-domain.com/ws',
    theme: 'blue',
    showBubble: true
  });
</script>
```

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MYSQL_HOST` | MySQL 主机 | localhost |
| `MYSQL_PORT` | MySQL 端口 | 3306 |
| `MILVUS_HOST` | Milvus 主机 | localhost |
| `MILVUS_PORT` | Milvus 端口 | 19530 |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `JWT_SECRET_KEY` | JWT 密钥 | - |

## 📝 默认账号

系统初始化时会创建默认角色：
- 管理员：可管理所有资源
- 客服：可处理工单
- 运营：可查看数据报表
- 普通用户：可创建工单

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

[MIT](LICENSE)

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://langchain.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Milvus](https://milvus.io/)
- [Ant Design](https://ant.design/)