# -----------------------------
# 构建阶段
# -----------------------------
FROM python:3.11-bullseye as builder

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/root/.local/bin:$PATH

# 清理默认源，改成阿里云源
RUN rm -f /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free" | tee /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" | tee -a /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" | tee -a /etc/apt/sources.list

# 更新 apt 并安装构建依赖
RUN apt-get clean \
    && apt-get update -o Acquire::Retries=3 -o Acquire::http::Timeout="10" \
    && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    liblzo2-dev \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖文件
COPY requirements.txt .
COPY AutoMdxBuilder_python/requirements.txt ./automdx_requirements.txt

# 安装 Python 依赖到 /root/.local
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r automdx_requirements.txt

# -----------------------------
# 运行阶段
# -----------------------------
FROM python:3.11-bullseye

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:/app/AutoMdxBuilder_python
ENV FLASK_APP=wsgi.py
ENV AMB_PATH=/usr/local/bin/AutoMdxBuilder

# 清理默认源，改成阿里云源
RUN rm -f /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free" | tee /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" | tee -a /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" | tee -a /etc/apt/sources.list

# 安装运行时依赖
RUN apt-get clean \
    && apt-get update -o Acquire::Retries=3 -o Acquire::http::Timeout="10" \
    && apt-get install -y --no-install-recommends \
    liblzo2-2 \
    mupdf-tools \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制构建阶段已安装的 Python 包
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 设置 AutoMdxBuilder 可执行
RUN chmod +x /app/AutoMdxBuilder_python/AutoMdxBuilder && \
    ln -sf /app/AutoMdxBuilder_python/AutoMdxBuilder /usr/local/bin/AutoMdxBuilder

# 创建目录并设置权限
RUN mkdir -p static/uploads static/output logs && \
    chmod -R 777 static/uploads static/output logs

# 暴露端口
EXPOSE 8000

# 默认启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "300", "wsgi:app"]