# 开发指南

## 项目结构

```
order_agent/                    # 项目根目录
├── backend/                    # Python FastAPI 后端
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── manage.py               # 管理脚本
│   ├── models/                 # 数据模型
│   ├── api/                    # API 路由
│   ├── agents/                 # LangGraph 智能体
│   ├── tools/                  # 工具函数
│   ├── websocket/              # WebSocket 管理
│   └── db/                     # 数据库连接
├── frontend-admin/             # React 管理后台
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   │   ├── ChatWorkplace/  # 客服工作台
│   │   │   ├── KnowledgeBase/  # 知识库管理
│   │   │   └── Tickets/        # 工单管理
│   │   ├── stores/             # Zustand 状态管理
│   │   └── services/           # API 服务
│   └── package.json
├── widget/                     # 嵌入式客服组件
│   ├── ticket-widget.js        # 核心组件
│   └── demo.html               # 演示页面
├── docker-compose.yml          # Docker 编排
├── manage.py                   # 项目管理脚本
└── start-backend.bat           # Windows 启动脚本
```

---

## 快速开始

### 1. 启动依赖服务

```bash
docker-compose up -d mysql milvus minio
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env 文件，填入你的配置
```

### 3. 初始化数据库

```bash
python manage.py init-db
```

### 4. 启动后端

**方式一：使用管理脚本（推荐）**
```bash
python manage.py run-backend
```

**方式二：使用 VS Code 调试**
1. 打开 VS Code
2. 安装 Python 插件
3. 按 `F5` 选择 `Run Backend` 即可启动

**方式三：手动设置 PYTHONPATH**

Windows:
```cmd
set PYTHONPATH=%CD%\backend
python -m uvicorn main:app --reload --port 8001
```

PowerShell:
```powershell
$env:PYTHONPATH="$PWD\backend"
python -m uvicorn main:app --reload --port 8001
```

**方式四：使用批处理文件**
双击运行 `start-backend.bat`

后端将在 http://localhost:8001 运行
API 文档: http://localhost:8001/docs

### 5. 启动前端

```bash
cd frontend-admin
npm install
npm run dev
```

前端将在 http://localhost:5173 运行

### 6. 测试 Widget

打开 `widget/demo.html` 文件，或使用本地服务器：

```bash
cd widget
python -m http.server 8080
```

访问 http://localhost:8080/demo.html

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

## 解决 Python 导入问题

### 错误：`ModuleNotFoundError: No module named 'config'`

**原因**：Python 找不到 backend 目录

**解决**：
1. 确保 backend 目录下有 `__init__.py` 文件
2. 设置 PYTHONPATH 包含 backend 目录
3. 使用管理脚本运行

### 错误：`ImportError: attempted relative import with no known parent package`

**原因**：使用了相对导入但 Python 没有识别到包

**解决**：
1. 使用 `python -m` 方式运行模块
2. 或者改为绝对导入
3. 使用管理脚本自动处理

---

## Claude Code 使用建议

在 Claude Code 中，使用以下方式确保导入正确：

```python
# 在对话中先设置路径
import sys
sys.path.insert(0, './backend')

# 然后正常导入
from config import settings
from models import User
```

或者在对话开始时告诉 Claude：

> 请先执行 `export PYTHONPATH="./backend:$PYTHONPATH"`，然后再分析代码

---

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

---

## 开发工作流

### 后端开发

1. 修改代码后自动重载（已配置 `--reload`）
2. 访问 http://localhost:8001/docs 查看 API 文档
3. 使用 VS Code 调试配置进行断点调试

### 前端开发

1. 修改代码后热更新（HMR）
2. 使用 React DevTools 调试组件
3. 使用浏览器开发者工具查看网络请求

### Widget 开发

1. 修改 `widget/ticket-widget.js`
2. 刷新 `demo.html` 查看效果
3. 使用浏览器开发者工具调试 Shadow DOM

---

## 调试技巧

### WebSocket 调试

1. 打开浏览器开发者工具
2. 切换到 Network 标签
3. 筛选 WS (WebSocket) 请求
4. 查看 Messages 标签中的实时消息

### 查看日志

后端日志：
```bash
# 实时查看日志
tail -f logs/app.log

# Windows
type logs\app.log
```

---

## 部署

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署

1. 后端：
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

2. 前端：
```bash
cd frontend-admin
npm install
npm run build
# 将 dist 目录部署到 Nginx
```

3. Widget：
```bash
# 将 widget 目录部署到 CDN 或静态服务器
cp widget/ticket-widget.js /var/www/html/
```

---

## 常见问题

### 1. 数据库连接失败
- 检查 MySQL 是否已启动：`docker-compose ps`
- 检查环境变量配置是否正确
- 检查数据库是否已初始化：`python manage.py init-db`

### 2. Milvus 连接失败
- 检查 Milvus 是否已启动
- 检查 MILVUS_HOST 和 MILVUS_PORT 配置

### 3. WebSocket 连接失败
- 检查后端服务是否正常运行
- 检查防火墙设置
- 检查 Token 是否有效

### 4. 前端 API 请求失败
- 检查后端服务是否正常运行
- 检查 API 地址配置（通常是 http://localhost:8001）
- 检查是否已登录（Token 是否有效）