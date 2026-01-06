#!/bin/bash
# AutoMdxBuilder Web 本地开发环境快速启动脚本

set -e

echo "============================================="
echo "AutoMdxBuilder Web 开发环境启动"
echo "============================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查Redis
echo ""
echo "1. 检查Redis..."
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis未安装"
    echo ""
    echo "请先安装Redis:"
    echo "  macOS:   brew install redis"
    echo "  Ubuntu:  sudo apt-get install redis-server"
    echo ""
    exit 1
fi

# 检查Redis是否运行
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis未运行，正在启动..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    else
        sudo systemctl start redis
    fi
    sleep 2
fi

if redis-cli ping &> /dev/null; then
    echo "✅ Redis运行正常"
else
    echo "❌ Redis启动失败"
    exit 1
fi

# 检查虚拟环境
echo ""
echo "2. 检查Python虚拟环境..."
if [ ! -d "venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "3. 安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
echo "✅ 依赖安装完成"

# 检查.env文件
echo ""
echo "4. 检查配置文件..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，正在创建..."
    cp .env.example .env
    # 设置AMB_PATH
    AMB_PATH_DEFAULT="$SCRIPT_DIR/AutoMdxBuilder"
    sed -i.bak "s|AMB_PATH=.*|AMB_PATH=$AMB_PATH_DEFAULT|" .env
    rm .env.bak 2>/dev/null || true
    echo "✅ .env文件创建完成"
    echo "   请确保AutoMdxBuilder文件在: $AMB_PATH_DEFAULT"
else
    echo "✅ .env文件已存在"
fi

# 检查AutoMdxBuilder
echo ""
echo "5. 检查AutoMdxBuilder..."
AMB_PATH=$(grep AMB_PATH .env | cut -d '=' -f2)
if [ -f "$AMB_PATH" ]; then
    chmod +x "$AMB_PATH"
    echo "✅ AutoMdxBuilder找到: $AMB_PATH"
else
    echo "⚠️  AutoMdxBuilder未找到: $AMB_PATH"
    echo "   请将AutoMdxBuilder复制到该位置，或修改.env中的AMB_PATH"
fi

# 创建必要的目录
echo ""
echo "6. 创建必要的目录..."
mkdir -p static/uploads static/output logs
echo "✅ 目录创建完成"

echo ""
echo "============================================="
echo "准备完成！"
echo "============================================="
echo ""
echo "接下来，请在3个终端窗口中分别运行："
echo ""
echo "终端 1 - Flask Web:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  python wsgi.py"
echo ""
echo "终端 2 - Celery Worker:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  celery -A app.tasks.celery_app worker --loglevel=info"
echo ""
echo "终端 3 - Celery Beat (可选):"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  celery -A app.tasks.celery_app beat --loglevel=info"
echo ""
echo "然后访问: http://localhost:8000"
echo ""
echo "或使用tmux一键启动: ./启动全部服务.sh"
echo ""
