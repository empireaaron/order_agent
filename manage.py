#!/usr/bin/env python3
"""
项目启动管理脚本
使用方式: python manage.py [command]

Commands:
    run-backend     - 启动后端服务（端口 8001）
    run-frontend    - 启动前端开发服务器
    init-db         - 初始化数据库
    test            - 运行测试（pytest）
    lint            - 代码检查（ruff + eslint）
"""
import sys
import os
import subprocess

# 将 backend 添加到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_backend():
    """启动后端服务"""
    os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
    subprocess.run([sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8001'])

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

def run_tests():
    """运行测试"""
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    result = subprocess.run([sys.executable, '-m', 'pytest', backend_dir, '-v'])
    sys.exit(result.returncode)

def run_lint():
    """代码检查"""
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend-admin')

    has_error = False

    # 后端：优先尝试 ruff，否则尝试 flake8
    try:
        if subprocess.run(['ruff', 'check', backend_dir]).returncode != 0:
            has_error = True
    except FileNotFoundError:
        print("ruff 未找到，尝试使用 flake8...")
        try:
            if subprocess.run(['flake8', backend_dir]).returncode != 0:
                has_error = True
        except FileNotFoundError:
            print("flake8 也未找到，跳过后端代码检查")
            has_error = True

    # 前端：eslint
    if os.path.exists(frontend_dir):
        try:
            if subprocess.run(['npm', 'run', 'lint'], cwd=frontend_dir).returncode != 0:
                has_error = True
        except FileNotFoundError:
            print("npm 未找到，跳过前端代码检查")
            has_error = True

    sys.exit(1 if has_error else 0)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    commands = {
        'run-backend': run_backend,
        'run-frontend': run_frontend,
        'init-db': init_db,
        'test': run_tests,
        'lint': run_lint,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"未知命令: {command}")
        print(__doc__)

if __name__ == '__main__':
    main()