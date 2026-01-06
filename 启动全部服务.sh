#!/bin/bash
# 使用tmux一键启动所有服务

set -e

echo "============================================="
echo "AutoMdxBuilder Web - 一键启动所有服务"
echo "============================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查tmux
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux未安装"
    echo ""
    echo "请先安装tmux:"
    echo "  macOS:   brew install tmux"
    echo "  Ubuntu:  sudo apt-get install tmux"
    echo ""
    echo "或者手动在3个终端中启动服务（参见 本地开发指南.md）"
    exit 1
fi

# 先运行准备脚本
echo ""
echo "运行准备脚本..."
./启动开发环境.sh

echo ""
echo "启动tmux会话..."

# 会话名称
SESSION="automdx_web"

# 杀死现有会话（如果存在）
tmux has-session -t $SESSION 2>/dev/null && tmux kill-session -t $SESSION

# 创建新会话
tmux new-session -d -s $SESSION -n "flask"

# 窗口1: Flask
tmux send-keys -t $SESSION:flask "cd $SCRIPT_DIR" C-m
tmux send-keys -t $SESSION:flask "source venv/bin/activate" C-m
tmux send-keys -t $SESSION:flask "python wsgi.py" C-m

# 窗口2: Celery Worker
tmux new-window -t $SESSION -n "celery"
tmux send-keys -t $SESSION:celery "cd $SCRIPT_DIR" C-m
tmux send-keys -t $SESSION:celery "source venv/bin/activate" C-m
tmux send-keys -t $SESSION:celery "celery -A app.tasks.celery_app worker --loglevel=info" C-m

# 窗口3: Celery Beat
tmux new-window -t $SESSION -n "beat"
tmux send-keys -t $SESSION:beat "cd $SCRIPT_DIR" C-m
tmux send-keys -t $SESSION:beat "source venv/bin/activate" C-m
tmux send-keys -t $SESSION:beat "celery -A app.tasks.celery_app beat --loglevel=info" C-m

# 窗口4: 日志查看
tmux new-window -t $SESSION -n "logs"
tmux send-keys -t $SESSION:logs "cd $SCRIPT_DIR" C-m
tmux send-keys -t $SESSION:logs "tail -f logs/app.log" C-m

# 回到第一个窗口
tmux select-window -t $SESSION:flask

echo ""
echo "============================================="
echo "所有服务已在tmux中启动！"
echo "============================================="
echo ""
echo "窗口说明:"
echo "  flask  - Flask Web服务 (端口 8000)"
echo "  celery - Celery Worker"
echo "  beat   - Celery Beat"
echo "  logs   - 日志查看"
echo ""
echo "访问应用: http://localhost:8000"
echo ""
echo "tmux操作:"
echo "  进入会话:  tmux attach -t $SESSION"
echo "  切换窗口:  Ctrl+b, 然后按数字 (0-3)"
echo "  退出会话:  Ctrl+b, 然后按 d"
echo "  停止所有:  tmux kill-session -t $SESSION"
echo ""
echo "正在连接到tmux会话..."
sleep 2
tmux attach -t $SESSION
