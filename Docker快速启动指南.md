# Docker 快速启动指南

## 安装 Docker Desktop

### 1. 下载 Docker Desktop for Mac

**方式1: 官网下载（推荐）**
- 访问: https://www.docker.com/products/docker-desktop
- 点击 "Download for Mac"
- 选择你的芯片类型：
  - Apple Silicon (M1/M2/M3): 下载 ARM64 版本
  - Intel芯片: 下载 AMD64 版本

**方式2: 使用 Homebrew**
```bash
brew install --cask docker
```

### 2. 安装 Docker Desktop

1. 打开下载的 `.dmg` 文件
2. 拖动 Docker 图标到 Applications 文件夹
3. 打开 Applications，双击 Docker
4. 等待 Docker 启动（首次启动需要几分钟）
5. 状态栏会出现 Docker 图标

### 3. 验证安装

打开终端，运行：
```bash
docker --version
docker-compose --version
```

应该看到类似输出：
```
Docker version 24.0.7
Docker Compose version 2.23.0
```

---

## 启动项目

### 1. 准备项目文件

```bash
cd /Users/lizhouyuan/E盘/MDX製作/電子辭典製作/AutoMdxBuilder_Web

# 复制 AutoMdxBuilder 可执行文件
cp /Users/lizhouyuan/E盘/MDX製作/AutoMdxBuilder/AutoMdxBuilder ./AutoMdxBuilder

# 确保有执行权限
chmod +x ./AutoMdxBuilder

# 验证文件存在
ls -lh AutoMdxBuilder
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 查看配置（已经配置好，通常不需要修改）
cat .env
```

### 3. 启动所有服务

```bash
# 一键启动（首次会下载镜像，需要几分钟）
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 4. 验证服务

```bash
# 查看运行的容器（应该看到5个容器）
docker-compose ps

# 应该显示：
# automdx_nginx    - running
# automdx_web      - running
# automdx_redis    - running
# automdx_celery   - running
# automdx_beat     - running
```

### 5. 访问应用

打开浏览器访问: **http://localhost**

---

## 常用命令

### 查看状态
```bash
# 查看所有容器状态
docker-compose ps

# 查看资源使用
docker stats
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f web        # Flask应用
docker-compose logs -f celery_worker   # Celery任务
docker-compose logs -f nginx      # Nginx
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart web
```

### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 更新服务
```bash
# 重新构建并启动
docker-compose up -d --build

# 拉取最新镜像
docker-compose pull
docker-compose up -d
```

---

## 故障排查

### 容器启动失败

**查看详细错误**:
```bash
docker-compose logs web
```

**常见问题**:
1. **端口被占用**: 修改 `docker-compose.yml` 中的端口
2. **AutoMdxBuilder未找到**: 确保文件在项目根目录
3. **权限问题**: 运行 `chmod +x AutoMdxBuilder`

### 清理并重新启动

```bash
# 停止所有容器
docker-compose down

# 删除所有容器和数据卷
docker-compose down -v

# 清理Docker缓存（如果需要）
docker system prune -a

# 重新启动
docker-compose up -d --build
```

### 进入容器调试

```bash
# 进入Web容器
docker-compose exec web bash

# 进入Celery容器
docker-compose exec celery_worker bash

# 在容器内可以运行Python、查看文件等
```

---

## 性能优化

### 资源限制

如果电脑配置不高，可以在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  web:
    mem_limit: 1g
    cpus: 1
```

### 磁盘清理

定期清理不用的镜像和容器：
```bash
# 清理停止的容器
docker container prune

# 清理不用的镜像
docker image prune -a

# 清理所有未使用的资源
docker system prune -a --volumes
```

---

## 生产环境部署

本地Docker配置和生产环境完全一致！

部署到阿里云时：
```bash
# 1. 上传项目到服务器
rsync -avz ./ root@your-ip:/opt/automdxbuilder/

# 2. SSH连接服务器
ssh root@your-ip

# 3. 运行部署脚本
cd /opt/automdxbuilder
./deploy/setup_server.sh
./deploy/aliyun_deploy.sh

# 完成！
```

---

## 开发工作流

### 修改代码后

```bash
# 1. 重新构建镜像
docker-compose build web

# 2. 重启服务
docker-compose up -d

# 或一步完成
docker-compose up -d --build
```

### 添加Python依赖

```bash
# 1. 修改 requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. 重新构建
docker-compose build

# 3. 重启
docker-compose up -d
```

---

## 总结

**启动**: `docker-compose up -d`
**停止**: `docker-compose down`
**日志**: `docker-compose logs -f`
**访问**: http://localhost

简单！高效！专业！
