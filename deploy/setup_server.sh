#!/bin/bash
# 阿里云ECS服务器初始化脚本
# 用途：安装Docker、Docker Compose等必要软件

set -e

echo "==========================================="
echo "AutoMdxBuilder Web 服务器初始化"
echo "==========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root用户运行此脚本"
    exit 1
fi

# 更新系统
echo "1. 更新系统..."
apt-get update
apt-get upgrade -y

# 安装基础工具
echo "2. 安装基础工具..."
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release

# 安装Docker
echo "3. 安装Docker..."
if ! command -v docker &> /dev/null; then
    # 添加Docker官方GPG密钥
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # 设置Docker仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 安装Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # 启动Docker
    systemctl start docker
    systemctl enable docker

    echo "Docker安装完成"
else
    echo "Docker已安装"
fi

# 安装Docker Compose (standalone)
echo "4. 安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION="2.24.0"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose安装完成"
else
    echo "Docker Compose已安装"
fi

# 配置防火墙（如果使用ufw）
echo "5. 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    echo "防火墙规则已配置"
fi

# 创建应用目录
echo "6. 创建应用目录..."
mkdir -p /opt/automdxbuilder
chown -R $SUDO_USER:$SUDO_USER /opt/automdxbuilder

# 配置系统限制
echo "7. 配置系统限制..."
cat >> /etc/security/limits.conf <<EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 4096
* hard nproc 4096
EOF

# 优化内核参数
cat >> /etc/sysctl.conf <<EOF
vm.max_map_count=262144
net.core.somaxconn=1024
net.ipv4.tcp_max_syn_backlog=2048
EOF
sysctl -p

echo "==========================================="
echo "服务器初始化完成！"
echo "==========================================="
echo ""
echo "下一步："
echo "1. 上传AutoMdxBuilder可执行文件到 /opt/automdxbuilder/AutoMdxBuilder"
echo "2. 上传应用代码到 /opt/automdxbuilder"
echo "3. 运行部署脚本 ./deploy/aliyun_deploy.sh"
echo ""
