# 开发指南

## 项目结构

```
order_agent/                    # 项目根目录
├── backend/                    # Python 后端
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置
│   ├── models/                 # 数据模型
│   ├── api/                    # API 路由
│   └── ...
├── frontend-admin/             # React 前端
│   ├── src/
│   └── package.json
├── widget/                     # 嵌入式组件
├── .vscode/                    # VS Code 配置
├── manage.py                   # 管理脚本
└── .env                        # 环境变量
```

## 解决 Python 导入问题

### 方案 1：使用 VS Code（推荐）

VS Code 配置已自动设置好，直接使用即可：

1. 打开 VS Code
2. 安装 Python 插件
3. 按 `F5` 选择 `Run Backend` 即可启动

### 方案 2：使用管理脚本

```bash
# 初始化数据库
python manage.py init-db

# 启动后端
python manage.py run-backend

# 启动前端
python manage.py run-frontend
```

### 方案 3：手动设置 PYTHONPATH

**Windows:**
```cmd
set PYTHONPATH=%CD%\backend
python -m uvicorn main:app --reload
```

**PowerShell:**
```powershell
$env:PYTHONPATH="$PWD\backend"
python -m uvicorn main:app --reload
```

**Linux/Mac:**
```bash
export PYTHONPATH="$PWD/backend"
python -m uvicorn main:app --reload
```

### 方案 4：使用批处理文件

双击运行 `start-backend.bat`

## 开发工作流

### 1. 启动数据库

```bash
docker-compose up -d mysql milvus
```

### 2. 启动后端

```bash
python manage.py run-backend
```

后端将在 http://localhost:8000 运行
API 文档: http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend-admin
npm install
npm run dev
```

前端将在 http://localhost:3000 运行

## 常见导入错误解决

### 错误：`ModuleNotFoundError: No module named 'config'`

**原因**：Python 找不到 backend 目录

**解决**：
1. 确保 backend 目录下有 `__init__.py` 文件
2. 设置 PYTHONPATH 包含 backend 目录
3. 在 VS Code 中使用调试配置运行

### 错误：`ImportError: attempted relative import with no known parent package`

**原因**：使用了相对导入但 Python 没有识别到包

**解决**：
1. 使用 `python -m` 方式运行模块
2. 或者改为绝对导入

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

## 部署

### Docker 部署

```bash
docker-compose up -d
```

### 手动部署

1. 后端：
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. 前端：
```bash
cd frontend-admin
npm install
npm run build
```