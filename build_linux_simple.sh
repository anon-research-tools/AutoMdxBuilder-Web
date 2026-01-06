#!/bin/bash
# 方案B: 直接使用 Python 源码版本（无需编译）
# 这个脚本会准备一个可以在 Linux 上直接运行的 Python 版本

set -e

echo "=========================================="
echo "准备 Python 源码版本的 AutoMdxBuilder"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build_automdx_python"
OUTPUT_DIR="${SCRIPT_DIR}/AutoMdxBuilder_python"

# 清理
rm -rf "$BUILD_DIR" "$OUTPUT_DIR"
mkdir -p "$BUILD_DIR"

cd "$BUILD_DIR"

# 下载源代码
echo "1. 下载 AutoMdxBuilder 源代码..."
git clone https://github.com/Litles/AutoMdxBuilder.git
cd AutoMdxBuilder

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 复制必要文件
echo "2. 复制源代码文件..."
cp -r ./* "$OUTPUT_DIR/"

# 创建启动包装脚本
echo "3. 创建启动脚本..."
cat > "$OUTPUT_DIR/AutoMdxBuilder" << 'EOF'
#!/usr/bin/env python3
"""
AutoMdxBuilder 启动脚本 (Linux 版本)
使用 Python 直接运行
"""
import sys
import os

# 将当前目录添加到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 导入并运行主程序
if __name__ == '__main__':
    # 尝试导入 main.py
    try:
        import main
        main.main() if hasattr(main, 'main') else exec(open(os.path.join(script_dir, 'main.py')).read())
    except ImportError:
        # 如果没有 main.py，查找其他入口
        import subprocess
        # 查找 .py 文件
        py_files = [f for f in os.listdir(script_dir) if f.endswith('.py') and f != 'setup.py']
        if py_files:
            exec(open(os.path.join(script_dir, py_files[0])).read())
        else:
            print("错误: 找不到入口文件", file=sys.stderr)
            sys.exit(1)
EOF

chmod +x "$OUTPUT_DIR/AutoMdxBuilder"

# 创建 requirements.txt（如果不存在）
if [ ! -f "$OUTPUT_DIR/requirements.txt" ]; then
    echo "4. 创建 requirements.txt..."
    cat > "$OUTPUT_DIR/requirements.txt" << 'EOF'
mdict-utils
PyMuPDF
Pillow
opencc-python-reimplemented
toml
EOF
fi

# 清理
cd "$SCRIPT_DIR"
rm -rf "$BUILD_DIR"

echo ""
echo "=========================================="
echo "准备完成！"
echo "=========================================="
echo ""
echo "Python 版本的 AutoMdxBuilder 已准备好:"
echo "  位置: $OUTPUT_DIR"
echo ""
echo "在 Linux 服务器上的使用方法:"
echo "1. 上传整个目录到服务器:"
echo "   scp -r AutoMdxBuilder_python root@服务器IP:/opt/automdxbuilder/"
echo ""
echo "2. 在服务器上安装依赖:"
echo "   cd /opt/automdxbuilder/AutoMdxBuilder_python"
echo "   pip3 install -r requirements.txt"
echo ""
echo "3. 使用方法:"
echo "   ./AutoMdxBuilder 或 python3 main.py"
echo ""
