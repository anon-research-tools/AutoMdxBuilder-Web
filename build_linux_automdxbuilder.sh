#!/bin/bash
# 使用 Docker 编译 Linux 版本的 AutoMdxBuilder
# 这个脚本会下载源代码并在 Linux 容器中编译

set -e

echo "=========================================="
echo "编译 Linux 版本的 AutoMdxBuilder"
echo "=========================================="

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build_automdx"
OUTPUT_FILE="${SCRIPT_DIR}/AutoMdxBuilder_linux"

# 清理之前的构建
if [ -d "$BUILD_DIR" ]; then
    echo "清理旧的构建目录..."
    rm -rf "$BUILD_DIR"
fi

# 创建构建目录
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# 1. 下载 AutoMdxBuilder 源代码
echo "1. 下载 AutoMdxBuilder 源代码..."
git clone https://github.com/Litles/AutoMdxBuilder.git
cd AutoMdxBuilder

# 2. 创建 Dockerfile 用于编译
echo "2. 创建编译环境..."
cat > Dockerfile.build << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmupdf-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 PyInstaller
RUN pip install --no-cache-dir pyinstaller

# 复制源代码
COPY . /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir mdict-utils PyMuPDF Pillow opencc-python-reimplemented toml

# 编译可执行文件
RUN pyinstaller --onefile --name AutoMdxBuilder \
    --add-data "lib:lib" \
    --hidden-import=fitz \
    --hidden-import=PIL \
    --hidden-import=opencc \
    main.py || \
    pyinstaller --onefile --name AutoMdxBuilder *.py

WORKDIR /app/dist

CMD ["ls", "-lah"]
EOF

# 3. 构建 Docker 镜像并编译
echo "3. 构建 Docker 镜像并编译 AutoMdxBuilder..."
docker build -f Dockerfile.build -t automdx-builder .

# 4. 从容器中提取编译好的文件
echo "4. 提取编译好的可执行文件..."
CONTAINER_ID=$(docker create automdx-builder)
docker cp ${CONTAINER_ID}:/app/dist/AutoMdxBuilder "$OUTPUT_FILE"
docker rm ${CONTAINER_ID}

# 5. 设置执行权限
chmod +x "$OUTPUT_FILE"

# 6. 清理
echo "5. 清理构建目录..."
cd "$SCRIPT_DIR"
rm -rf "$BUILD_DIR"

# 7. 验证
echo ""
echo "=========================================="
echo "编译完成！"
echo "=========================================="
echo ""
echo "Linux 版本的 AutoMdxBuilder 已生成:"
echo "  位置: $OUTPUT_FILE"
echo "  大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "验证文件类型:"
file "$OUTPUT_FILE"
echo ""
echo "下一步:"
echo "1. 将此文件上传到阿里云服务器"
echo "2. scp AutoMdxBuilder_linux root@你的服务器IP:/opt/automdxbuilder/AutoMdxBuilder"
echo ""
