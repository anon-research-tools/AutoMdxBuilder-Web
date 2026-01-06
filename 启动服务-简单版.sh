#!/bin/bash
# AutoMdxBuilder Web - 简单启动脚本（不需要tmux）
# 所有服务在后台运行

set -e

echo "============================================="
echo "AutoMdxBuilder Web - 后台启动所有服务"
echo "============================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 先运行准备脚本
echo ""
echo "1. 准备环境..."
./启动开发环境.sh

echo ""
echo "2. 启动服务..."

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p logs

# 停止旧进程（如果存在）
echo "停止旧进程..."
pkill -f "python wsgi.py" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
sleep 2

# 启动Flask（后台）
echo "启动Flask Web..."
nohup python wsgi.py > logs/flask.log 2>&1 &
FLASK_PID=$!
echo "  Flask PID: $FLASK_PID"

# 等待Flask启动
sleep 3

# 启动Celery Worker（后台）
echo "启动Celery Worker..."
nohup celery -A app.tasks.celery_app worker --loglevel=info > logs/celery.log 2>&1 &
CELERY_PID=$!
echo "  Celery PID: $CELERY_PID"

# 启动Celery Beat（后台）
echo "启动Celery Beat..."
nohup celery -A app.tasks.celery_app beat --loglevel=info > logs/beat.log 2>&1 &
BEAT_PID=$!
echo "  Beat PID: $BEAT_PID"

# 等待服务启动
sleep 3

echo ""
echo "============================================="
echo "所有服务已启动！"
echo "============================================="
echo ""
echo "服务状态:"
echo "  Flask Web:     运行中 (PID: $FLASK_PID)"
echo "  Celery Worker: 运行中 (PID: $CELERY_PID)"
echo "  Celery Beat:   运行中 (PID: $BEAT_PID)"
echo ""
echo "访问应用: http://localhost:8000"
echo ""
echo "查看日志:"
echo "  Flask:  tail -f logs/flask.log"
echo "  Celery: tail -f logs/celery.log"
echo "  Beat:   tail -f logs/beat.log"
echo ""
echo "停止服务:"
echo "  ./停止所有服务.sh"
echo "  或手动: pkill -f 'python wsgi.py' && pkill -f 'celery'"
echo ""

# 保存PID到文件
echo $FLASK_PID > logs/flask.pid
echo $CELERY_PID > logs/celery.pid
echo $BEAT_PID > logs/beat.pid

echo "PID已保存到 logs/*.pid"
echo ""
