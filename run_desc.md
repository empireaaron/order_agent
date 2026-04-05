项目运行指南

  方式一：使用 Docker Compose（推荐）

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

  方式二：本地开发运行

  1. 启动 MySQL 和 Milvus

  MySQL（Windows）：
  # 如果你有 MySQL 本地安装
  # 创建数据库
  mysql -u root -p
  CREATE DATABASE ticket_bot CHARACTER SET utf8mb4;

  Milvus（Docker）：
  # 只启动 Milvus（需要 etcd 和 minio）
  docker run -d --name milvus-standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest

  2. 后端启动

  # 进入后端目录
  cd backend

  # 创建虚拟环境
  python -m venv venv

  # 激活虚拟环境（Windows）
  .venv\Scripts\activate

  # 安装依赖（使用国内镜像加速）
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

  # 配置环境变量
  cp .env.example .env
  # 编辑 .env 填入你的配置

  # 初始化数据库
  # 方式1：使用 SQL 脚本
  mysql -u root -p ticket_bot < database.sql

  # 方式2：使用 Python
  python -c "from db.session import init_db; init_db()"

  # 启动后端
  uvicorn main:app --reload --host 0.0.0.0 --port 8001

  3. 前端启动

  # 新终端窗口，进入前端目录
  cd frontend-admin

  # 安装依赖（使用 pnpm 或 npm）
  npm install -g pnpm
  pnpm install

  # 启动开发服务器
  pnpm dev
  cd frontend-admin
  npm install
  npm run dev
  访问地址

  服务启动后：
  - 前端管理后台：http://localhost:3000
  - 后端 API：http://localhost:8001
  - API 文档：http://localhost:8001/docs
  ┌─────────────────────┬────────────────────────────────────┐                                                                                                                      
  │      文档类型       │                地址                │
  ├─────────────────────┼────────────────────────────────────┤                                                                                                                      
  │ Swagger UI (交互式) │ http://localhost:8001/docs         │                                                                                                                      
  ├─────────────────────┼────────────────────────────────────┤                                                                                                                      
  │ ReDoc (只读)        │ http://localhost:8001/redoc        │
  ├─────────────────────┼────────────────────────────────────┤
  │ OpenAPI JSON        │ http://localhost:8001/openapi.json │
  └─────────────────────┴────────────────────────────────────┘
  - Widget 演示：直接打开 widget/demo.html

  快速测试

  # 1. 创建测试用户
  curl -X POST http://localhost:8001/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
      "username": "admin",
      "email": "admin@example.com",
      "password": "admin123",
      "full_name": "管理员"
    }'

  # 2. 登录
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123"

  # 3. 创建工单
  curl -X POST http://localhost:8001/api/v1/tickets/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '{
      "title": "测试工单",
      "content": "这是一个测试问题",
      "priority": "normal",
      "category": "technical"
    }'

  常见问题

  ┌─────────────────┬────────────────────────────────────────────────────────────────────┐
  │      问题       │                              解决方案                              │
  ├─────────────────┼────────────────────────────────────────────────────────────────────┤
  │ pip 安装慢      │ 使用镜像：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple  │
  ├─────────────────┼────────────────────────────────────────────────────────────────────┤
  │ MySQL 连接失败  │ 检查 .env 中的 MYSQL_HOST 是否为 localhost 或 host.docker.internal │
  ├─────────────────┼────────────────────────────────────────────────────────────────────┤
  │ Milvus 连接失败 │ 确保 Milvus 容器已启动：docker ps                                  │
  ├─────────────────┼────────────────────────────────────────────────────────────────────┤
  │ 端口被占用      │ 修改端口：uvicorn main:app --port 8001                             │
  └─────────────────┴────────────────────────────────────────────────────────────────────┘

  需要我详细说明某个具体步骤吗？
