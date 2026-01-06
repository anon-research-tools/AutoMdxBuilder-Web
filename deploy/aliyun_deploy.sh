#!/bin/bash
# AutoMdxBuilder Web 阿里云部署脚本

set -e

echo "==========================================="
echo "AutoMdxBuilder Web 部署脚本"
echo "==========================================="

# 配置变量
APP_DIR="/opt/automdxbuilder"
REPO_URL="https://github.com/yourusername/AutoMdxBuilder_Web.git"  # 修改为你的仓库地址

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    echo "请先运行: sudo ./deploy/setup_server.sh"
    exit 1
fi

# 进入应用目录
cd $APP_DIR

# 拉取最新代码（如果使用Git）
# echo "1. 拉取最新代码..."
# git pull origin main

# 检查AutoMdxBuilder可执行文件
echo "1. 检查AutoMdxBuilder..."
if [ ! -f "$APP_DIR/AutoMdxBuilder" ]; then
    echo "错误: 未找到AutoMdxBuilder可执行文件"
    echo "请将AutoMdxBuilder上传到: $APP_DIR/AutoMdxBuilder"
    exit 1
fi
chmod +x $APP_DIR/AutoMdxBuilder

# 创建.env文件
echo "2. 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secret-key-here-change-this-in-production/$SECRET_KEY/" .env
    echo ".env文件已创建，请根据需要修改配置"
fi

# 创建必要的目录
echo "3. 创建必要的目录..."
mkdir -p static/uploads static/output logs ssl

# 停止现有容器
echo "4. 停止现有服务..."
docker-compose down || true

# 构建镜像
echo "5. 构建Docker镜像..."
docker-compose build

# 启动服务
echo "6. 启动服务..."
docker-compose up -d

# 等待服务启动
echo "7. 等待服务启动..."
sleep 10

# 检查服务状态
echo "8. 检查服务状态..."
docker-compose ps

# 检查日志
echo "9. 最近的日志..."
docker-compose logs --tail=20

echo "==========================================="
echo "部署完成！"
echo "==========================================="
echo ""
echo "服务访问地址:"
echo "  HTTP: http://$(curl -s ifconfig.me)"
echo ""
echo "有用的命令:"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose down"
echo "  查看状态: docker-compose ps"
echo ""
echo "注意:"
echo "1. 如果需要HTTPS，请配置SSL证书"
echo "2. 建议配置定时任务清理旧文件"
echo "3. 定期备份用户数据"
echo ""
