# 项目运行指南

## 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

---

## 方式一：使用 Docker Compose（推荐生产环境）

```bash
# 1. 确保在项目根目录
cd E:\PythonProject\order_agent

# 2. 复制环境变量配置
cp backend/.env.example backend/.env

# 3. 编辑 .env 文件，填入你的配置
# 至少配置：
# - MYSQL_PASSWORD
# - OPENAI_API_KEY 或 ANTHROPIC_API_KEY
# - JWT_SECRET_KEY

# 4. 启动所有服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f

# 6. 停止服务
docker-compose down
```

---

## 方式二：本地开发运行（推荐开发）

### 1. 启动依赖服务

```bash
# 启动 MySQL、Milvus 和 MinIO
docker-compose up -d mysql milvus minio
```

### 2. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate

# 安装依赖（使用国内镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 初始化数据库
python manage.py init-db

# 或使用 SQL 脚本
mysql -u root -p ticket_bot < database.sql

# 启动后端（方式1：使用管理脚本）
python manage.py run-backend

# 启动后端（方式2：使用 uvicorn）
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
 Invoke-RestMethod -Uri "http://localhost:8001/api/v1/chat/clear-history" -Method POST -Headers @{"Authorization"="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTQ1YTM2Ny0yYzA4LTQ4ZTItYjE3Mi1hZTE2ZGVlYWJmMDAiLCJyb2xlIjoiY3VzdG9tZXIiLCJleHAiOjE3NzU1NTc1MjB9.4tc8BuXB0_mOYQe8pfmy5grQYZEBaXBGXi7TNM27Lo4"}
### 3. 前端启动

```bash
# 新终端窗口，进入前端目录
cd frontend-admin

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. Widget 测试

```bash
# 进入 widget 目录
cd widget

# 启动静态服务器
python -m http.server 8080

# 或直接使用浏览器打开 demo.html
```

---

## 访问地址

服务启动后：

| 服务 | 地址 |
|------|------|
| 前端管理后台 | http://localhost:5173 |
| 后端 API | http://localhost:8001 |
| API 文档 (Swagger) | http://localhost:8001/docs |
| API 文档 (ReDoc) | http://localhost:8001/redoc |
| Widget 演示 | http://localhost:8080/demo.html |

---

## 快速测试

### 1. 创建测试用户

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "full_name": "管理员"
  }'
```

### 2. 登录

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 3. 创建工单

```bash
curl -X POST http://localhost:8001/api/v1/tickets/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "测试工单",
    "content": "这是一个测试问题",
    "priority": "normal",
    "category": "technical"
  }'
```

### 4. 创建聊天会话（转人工）

```bash
curl -X POST http://localhost:8001/api/v1/chat-service/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "request_type": "general",
    "message": "测试消息"
  }'
```

---

## 常用命令

```bash
# 初始化数据库
python manage.py init-db

# 启动后端
python manage.py run-backend

# 启动前端
python manage.py run-frontend

# 同时启动前后端
python manage.py run-all
```

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| pip 安装慢 | 使用镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| MySQL 连接失败 | 检查 .env 中的 MYSQL_HOST 是否为 localhost |
| Milvus 连接失败 | 确保 Milvus 容器已启动：`docker ps` |
| 401 Unauthorized | 检查 token 是否过期，重新登录 |
| WebSocket 连接失败 | 检查后端服务是否正常运行，token 是否有效 |
| 端口被占用 | 修改端口：`uvicorn main:app --port 8002` |

---

## 默认端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8001 | FastAPI 服务 |
| 前端开发 | 5173 | Vite 开发服务器 |
| Widget 演示 | 8080 | Python HTTP 服务器 |
| MySQL | 3306 | 数据库 |
| Milvus | 19530 | 向量数据库 |
| MinIO API | 9000 | 文件存储 API |
| MinIO Console | 9001 | 文件存储控制台 |