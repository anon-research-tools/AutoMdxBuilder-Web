#!/bin/bash
# 打包项目文件准备部署到阿里云

set -e

echo "=========================================="
echo "打包 AutoMdxBuilder_Web 项目"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="AutoMdxBuilder_Web"
OUTPUT_FILE="${PARENT_DIR}/${PROJECT_NAME}_deploy.tar.gz"

cd "$SCRIPT_DIR"

echo "1. 清理临时文件..."
# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# 清理 Mac 特定文件
find . -name ".DS_Store" -delete 2>/dev/null || true

# 清理构建目录
rm -rf build_automdx build_automdx_python 2>/dev/null || true

echo "2. 打包项目文件..."
cd "$PARENT_DIR"

tar -czf "$OUTPUT_FILE" \
    --exclude="${PROJECT_NAME}/.venv" \
    --exclude="${PROJECT_NAME}/venv" \
    --exclude="${PROJECT_NAME}/__pycache__" \
    --exclude="${PROJECT_NAME}/.pytest_cache" \
    --exclude="${PROJECT_NAME}/.git" \
    --exclude="${PROJECT_NAME}/.DS_Store" \
    --exclude="${PROJECT_NAME}/static/uploads/*" \
    --exclude="${PROJECT_NAME}/static/output/*" \
    --exclude="${PROJECT_NAME}/logs/*" \
    --exclude="${PROJECT_NAME}/*.log" \
    --exclude="${PROJECT_NAME}/AutoMdxBuilder" \
    --exclude="${PROJECT_NAME}/build_automdx*" \
    --exclude="${PROJECT_NAME}/*_deploy.tar.gz" \
    "$PROJECT_NAME"

echo ""
echo "=========================================="
echo "打包完成！"
echo "=========================================="
echo ""
echo "文件信息:"
ls -lh "$OUTPUT_FILE"
echo ""
echo "文件位置: $OUTPUT_FILE"
echo ""
echo "下一步:"
echo "1. 上传到阿里云服务器:"
echo "   scp $OUTPUT_FILE root@你的服务器IP:/opt/"
echo ""
echo "2. 在服务器上解压:"
echo "   cd /opt"
echo "   tar -xzf ${PROJECT_NAME}_deploy.tar.gz"
echo "   mv ${PROJECT_NAME} automdxbuilder"
echo ""
