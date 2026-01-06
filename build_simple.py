#!/usr/bin/env python3
"""
简化版一键打包脚本
"""
import os
import subprocess
import shutil
import platform
from pathlib import Path


def build():
    print("=" * 50)
    print("  AutoMdxBuilder 简化版打包工具")
    print("=" * 50)
    print()

    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    # 1. 清理旧构建
    print("[1/4] 清理旧构建...")
    for d in ['build', 'dist']:
        if Path(d).exists():
            shutil.rmtree(d)

    # 2. 检查依赖
    print("[2/4] 检查 PyInstaller...")
    try:
        import PyInstaller
        print(f"      PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("      正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 3. 运行 PyInstaller
    print("[3/4] 打包中（这需要几分钟）...")
    try:
        subprocess.check_call([
            "pyinstaller",
            "--noconfirm",
            "AutoMdxBuilder_Simple.spec"
        ])
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        return False

    # 4. 整理输出
    print("[4/4] 整理发布包...")
    dist_dir = Path("dist")
    release_dir = script_dir / "Release_Simple"

    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()

    if platform.system() == "Darwin":
        # macOS
        src_app = dist_dir / "AutoMdxBuilder.app"
        if src_app.exists():
            shutil.copytree(src_app, release_dir / "AutoMdxBuilder.app")

            # 创建说明文件
            readme = release_dir / "使用说明.txt"
            readme.write_text("""AutoMdxBuilder 电子词典制作工具
================================

使用方法：
1. 双击 AutoMdxBuilder.app 启动
2. 程序会自动打开浏览器
3. 在浏览器中操作即可

注意事项：
- 首次打开可能需要在"系统设置 > 隐私与安全性"中允许运行
- 关闭终端窗口会停止服务
- 生成的文件保存在程序同目录的 static 文件夹中

如有问题请联系开发者。
""", encoding='utf-8')

    else:
        # Windows
        src_dir = dist_dir / "AutoMdxBuilder"
        if src_dir.exists():
            shutil.copytree(src_dir, release_dir / "AutoMdxBuilder")

            readme = release_dir / "使用说明.txt"
            readme.write_text("""AutoMdxBuilder 电子词典制作工具
================================

使用方法：
1. 进入 AutoMdxBuilder 文件夹
2. 双击 AutoMdxBuilder.exe 启动
3. 程序会自动打开浏览器
4. 在浏览器中操作即可

注意事项：
- 关闭黑色窗口会停止服务
- 生成的文件保存在程序目录的 static 文件夹中

如有问题请联系开发者。
""", encoding='utf-8')

    print()
    print("=" * 50)
    print(f"  打包成功！")
    print(f"  输出目录: {release_dir}")
    print()
    print("  你可以直接把 Release_Simple 文件夹")
    print("  发给朋友使用！")
    print("=" * 50)

    return True


if __name__ == "__main__":
    import sys
    success = build()
    if not success:
        print("\n按回车键退出...")
        input()
        sys.exit(1)
