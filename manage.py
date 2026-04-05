#!/usr/bin/env python3
"""
项目启动管理脚本
使用方式: python manage.py [command]

Commands:
    run-backend     - 启动后端服务
    run-frontend    - 启动前端开发服务器
    init-db         - 初始化数据库
    test            - 运行测试
    lint            - 代码检查
"""
import sys
import os
import subprocess

# 将 backend 添加到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_backend():
    """启动后端服务"""
    os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
    subprocess.run([sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'])

def run_frontend():
    """启动前端开发服务器"""
    os.chdir(os.path.join(os.path.dirname(__file__), 'frontend-admin'))
    subprocess.run(['npm', 'run', 'dev'])

def init_db():
    """初始化数据库"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    from db.session import init_db
    init_db()
    print("数据库初始化完成！")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    commands = {
        'run-backend': run_backend,
        'run-frontend': run_frontend,
        'init-db': init_db,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"未知命令: {command}")
        print(__doc__)

if __name__ == '__main__':
    main()