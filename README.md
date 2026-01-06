# AutoMdxBuilder Web

基于 Flask + Celery 的在线 MDX 词典制作平台

## 项目简介

AutoMdxBuilder Web 是 AutoMdxBuilder 的 Web 版本，允许用户通过浏览器上传 PDF 文件，自动转换并生成 MDX 格式的词典文件。

### 主要特性

- **在线处理**: 无需安装桌面软件，浏览器即可使用
- **异步任务**: 使用 Celery + Redis 处理耗时任务
- **实时进度**: WebSocket 实时显示转换和构建进度
- **自动清理**: 定时清理过期文件，节省存储空间
- **Docker 部署**: 一键部署到任何支持 Docker 的服务器
- **美观界面**: 现代化的响应式 Web 界面

### 技术栈

- **后端**: Flask 3.0
- **异步任务**: Celery 5.3 + Redis
- **PDF处理**: PyMuPDF (fitz)
- **图像处理**: Pillow
- **前端**: HTML5 + Bootstrap 5 + JavaScript
- **部署**: Docker + Docker Compose + Nginx
- **服务器**: Gunicorn

---

## 快速开始

### 本地开发

#### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/AutoMdxBuilder_Web.git
cd AutoMdxBuilder_Web

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 安装 Redis

**macOS**:
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows**:
下载并安装 [Redis for Windows](https://github.com/microsoftarchive/redis/releases)

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置 AMB_PATH 为 AutoMdxBuilder 可执行文件路径
```

#### 4. 启动服务

**终端 1 - Flask Web**:
```bash
source venv/bin/activate
python wsgi.py
```

**终端 2 - Celery Worker**:
```bash
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

**终端 3 - Celery Beat** (可选):
```bash
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

#### 5. 访问应用

打开浏览器访问: http://localhost:8000

---

### Docker 部署

#### 快速启动

```bash
# 1. 复制 AutoMdxBuilder 可执行文件到项目目录
cp /path/to/AutoMdxBuilder ./AutoMdxBuilder

# 2. 配置环境变量
cp .env.example .env

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问应用
# http://localhost
```

#### 常用命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 重新构建
docker-compose build
docker-compose up -d
```

---

### 阿里云部署

详细部署步骤请查看：[阿里云部署指南.md](阿里云部署指南.md)

**快速部署**:

```bash
# 1. SSH连接到服务器
ssh root@your-server-ip

# 2. 上传项目文件
rsync -avz ./ root@your-server-ip:/opt/automdxbuilder/

# 3. 运行初始化脚本
cd /opt/automdxbuilder
sudo ./deploy/setup_server.sh

# 4. 运行部署脚本
./deploy/aliyun_deploy.sh

# 5. 访问应用
# http://your-server-ip
```

---

## 使用指南

### 制作词典流程

1. **上传 PDF**
   - 点击或拖拽上传 PDF 文件
   - 支持最大 500MB 文件

2. **配置转换参数**
   - DPI: 控制图片分辨率 (200-400)
   - 质量: 图片质量 (75-95)
   - 自动裁剪: 去除页面白边

3. **开始转换**
   - 系统自动转换 PDF 为图片
   - 实时显示转换进度

4. **配置词典信息**
   - 词典名称
   - 作者
   - 描述

5. **生成 MDX**
   - 系统自动生成 MDX 文件
   - 下载词典文件

6. **导入词典**
   - 使用 MDict 等软件导入 MDX 文件

---

## 项目结构

```
AutoMdxBuilder_Web/
├── app/                        # Flask 应用
│   ├── __init__.py            # 应用初始化
│   ├── routes.py              # 路由和视图
│   └── tasks.py               # Celery 任务
├── core/                       # 核心处理模块
│   ├── pdf_processor.py       # PDF 处理
│   └── amb_executor.py        # MDX 构建
├── utils/                      # 工具模块
│   └── logger.py              # 日志系统
├── static/                     # 静态文件
│   ├── uploads/               # 上传文件
│   └── output/                # 输出文件
├── templates/                  # HTML 模板
│   └── index.html             # 主页
├── deploy/                     # 部署脚本
│   ├── setup_server.sh        # 服务器初始化
│   └── aliyun_deploy.sh       # 部署脚本
├── config.py                   # 配置文件
├── wsgi.py                     # WSGI 入口
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 镜像
├── docker-compose.yml          # Docker 编排
├── nginx.conf                  # Nginx 配置
└── README.md                   # 项目说明
```

---

## API 文档

### 上传文件
```
POST /api/upload
Content-Type: multipart/form-data

参数:
  file: PDF文件

返回:
  {
    "task_id": "uuid",
    "filename": "example.pdf",
    "message": "文件上传成功"
  }
```

### 转换 PDF
```
POST /api/convert
Content-Type: application/json

参数:
  {
    "task_id": "uuid",
    "dpi": 300,
    "quality": 85,
    "crop": false
  }

返回:
  {
    "task_id": "uuid",
    "celery_task_id": "celery-uuid",
    "message": "PDF转换任务已启动"
  }
```

### 构建 MDX
```
POST /api/build
Content-Type: application/json

参数:
  {
    "task_id": "uuid",
    "config": "TOML配置内容"
  }

返回:
  {
    "task_id": "uuid",
    "celery_task_id": "celery-uuid",
    "message": "MDX构建任务已启动"
  }
```

### 查询任务状态
```
GET /api/status/<celery_task_id>

返回:
  {
    "state": "PROGRESS",
    "current": 50,
    "total": 100,
    "status": "正在处理..."
  }
```

### 下载结果
```
GET /api/download/<task_id>

返回: MDX文件下载
```

### 清理任务
```
DELETE /api/cleanup/<task_id>

返回:
  {
    "message": "文件已清理"
  }
```

---

## 配置说明

### 环境变量 (.env)

```bash
# Flask配置
FLASK_ENV=production              # 运行模式: development/production
SECRET_KEY=your-secret-key        # 密钥（生产环境必须修改）

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AutoMdxBuilder路径
AMB_PATH=/usr/local/bin/AutoMdxBuilder

# 文件保留时间（小时）
FILE_RETENTION_HOURS=24
```

### 应用配置 (config.py)

- `UPLOAD_FOLDER`: 上传目录
- `OUTPUT_FOLDER`: 输出目录
- `MAX_CONTENT_LENGTH`: 最大上传大小 (默认 500MB)
- `ALLOWED_EXTENSIONS`: 允许的文件类型
- `PDF_DEFAULT_DPI`: 默认 DPI (300)
- `PDF_DEFAULT_QUALITY`: 默认质量 (85)

---

## 开发指南

### 添加新功能

1. **添加路由**：在 `app/routes.py` 中添加新路由
2. **添加任务**：在 `app/tasks.py` 中添加 Celery 任务
3. **添加模板**：在 `templates/` 中添加 HTML 模板
4. **测试**：编写测试用例

### 代码风格

- 遵循 PEP 8 规范
- 使用类型提示
- 编写文档字符串
- 添加必要的注释

### 测试

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_routes.py

# 查看覆盖率
pytest --cov=app tests/
```

---

## 常见问题

### 1. Redis 连接失败

**问题**: `ConnectionError: Error connecting to Redis`

**解决**:
```bash
# 检查 Redis 是否运行
redis-cli ping

# 启动 Redis
# macOS
brew services start redis

# Linux
sudo systemctl start redis
```

### 2. AutoMdxBuilder 未找到

**问题**: `未找到AutoMdxBuilder可执行文件`

**解决**:
- 检查 `.env` 中的 `AMB_PATH` 配置
- 确保 AutoMdxBuilder 文件存在且有执行权限
```bash
chmod +x /path/to/AutoMdxBuilder
```

### 3. 上传文件过大

**问题**: `Request Entity Too Large`

**解决**:
- 修改 `config.py` 中的 `MAX_CONTENT_LENGTH`
- 修改 `nginx.conf` 中的 `client_max_body_size`

### 4. PDF 转换失败

**问题**: 转换过程中出错

**解决**:
- 检查 PDF 文件是否损坏
- 查看日志: `docker-compose logs celery_worker`
- 降低 DPI 设置

---

## 性能优化

### 1. 增加 Worker 数量

```yaml
# docker-compose.yml
services:
  celery_worker:
    command: celery -A app.tasks.celery_app worker --concurrency=4
```

### 2. 配置 Redis 持久化

```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 2gb
```

### 3. 启用 Nginx 缓存

```nginx
# nginx.conf
location /static/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 安全建议

1. **修改默认密钥**: 在生产环境中修改 `SECRET_KEY`
2. **配置 HTTPS**: 使用 Let's Encrypt 免费证书
3. **限制上传大小**: 防止滥用
4. **定期清理**: 自动清理过期文件
5. **防火墙配置**: 只开放必要端口
6. **备份数据**: 定期备份用户数据

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 联系方式

- **作者**: Your Name
- **邮箱**: your-email@example.com
- **项目**: https://github.com/yourusername/AutoMdxBuilder_Web

---

## 更新日志

### v1.0.0 (2025-12-29)

- 初始版本发布
- 支持 PDF 上传和转换
- 支持 MDX 生成
- Docker 部署支持
- 阿里云部署脚本
- 完整的文档

---

## 致谢

- [AutoMdxBuilder](https://github.com/yourusername/AutoMdxBuilder) - 核心词典生成工具
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Celery](https://docs.celeryq.dev/) - 异步任务队列
- [Bootstrap](https://getbootstrap.com/) - UI 框架
