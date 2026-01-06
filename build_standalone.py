import os
import subprocess
import shutil
import platform
from pathlib import Path

def build():
    print("🚀 开始构建 AutoMdxBuilder Standalone...")
    
    # 1. 环境检查
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # 2. 清理旧构建
    for d in ['build', 'dist']:
        if Path(d).exists():
            print(f"清理 {d} 目录...")
            shutil.rmtree(d)
            
    # 3. 运行 PyInstaller
    print("📦 运行 PyInstaller 打包 (这可能需要几分钟)...")
    try:
        subprocess.check_call([
            "pyinstaller",
            "--noconfirm",
            "AutoMdxBuilder.spec"
        ])
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller 打包失败: {e}")
        return

    # 4. 整理最终产物
    dist_dir = Path("dist")
    final_output = script_dir / "Standalone_Release"
    if final_output.exists():
        shutil.rmtree(final_output)
    final_output.mkdir()

    print("🚚 正在整理最终发布包...")
    
    if platform.system() == "Darwin":
        # Mac 版本不仅仅需要 .app，还需要把 .env 示例带上
        src_app = dist_dir / "AutoMdxBuilder.app"
        if src_app.exists():
            shutil.copytree(src_app, final_output / "AutoMdxBuilder.app")
            # 在 app 同级放一个 README
            with open(final_output / "使用必读.txt", "w") as f:
                f.write("AutoMdxBuilder Mac 版一键启动器\n\n")
                f.write("使用方法：\n")
                f.write("1. 直接双击 AutoMdxBuilder.app 启动。\n")
                f.write("2. 程序会自动打开浏览器。\n")
                f.write("3. 所有的上传文件和生成的词典都会保存在此文件夹下的 static 目录（第一次运行后生成）。\n")
    else:
        # Windows
        src_dir = dist_dir / "AutoMdxBuilder"
        if src_dir.exists():
            shutil.copytree(src_dir, final_output / "AutoMdxBuilder")
            
    # 5. 复制必要的补丁或外部配置
    if Path(".env.example").exists():
        shutil.copy(".env.example", final_output / ".env")

    print("\n" + "="*45)
    print(f"✅ 构建成功！产物位置: {final_output}")
    print("您可以直接将 Standalone_Release 文件夹发给朋友。")
    print("="*45)

if __name__ == "__main__":
    build()
