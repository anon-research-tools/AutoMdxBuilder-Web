#!/bin/bash
# 停止所有服务

echo "停止AutoMdxBuilder Web服务..."

# 方法1: 使用保存的PID
if [ -f logs/flask.pid ]; then
    kill $(cat logs/flask.pid) 2>/dev/null && echo "✅ Flask已停止"
    rm logs/flask.pid
fi

if [ -f logs/celery.pid ]; then
    kill $(cat logs/celery.pid) 2>/dev/null && echo "✅ Celery Worker已停止"
    rm logs/celery.pid
fi

if [ -f logs/beat.pid ]; then
    kill $(cat logs/beat.pid) 2>/dev/null && echo "✅ Celery Beat已停止"
    rm logs/beat.pid
fi

# 方法2: 根据进程名强制停止（确保清理）
pkill -f "python wsgi.py" 2>/dev/null
pkill -f "celery.*worker" 2>/dev/null
pkill -f "celery.*beat" 2>/dev/null

echo ""
echo "所有服务已停止"
