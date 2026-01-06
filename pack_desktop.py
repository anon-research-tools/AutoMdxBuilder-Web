import os
import shutil
import subprocess
import platform
from pathlib import Path

def pack():
    # 确保在脚本所在目录运行
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print(f"开始打包 AutoMdxBuilder Desktop (工作目录: {script_dir})...")
    
    # 1. 准备目录
    dist_dir = Path("dist_package")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # 2. 复制核心文件
    print("复制应用程序文件...")
    shutil.copytree("app", dist_dir / "app", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree("core", dist_dir / "core", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree("utils", dist_dir / "utils", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree("static", dist_dir / "static", ignore=shutil.ignore_patterns("uploads/*", "output/*"))
    shutil.copytree("templates", dist_dir / "templates")
    shutil.copytree("AutoMdxBuilder_python", dist_dir / "AutoMdxBuilder_python", ignore=shutil.ignore_patterns("__pycache__", "_tmp/*"))
    
    shutil.copy("config.py", dist_dir)
    shutil.copy("wsgi.py", dist_dir)
    shutil.copy("desktop_launcher.py", dist_dir)
    if Path(".env").exists():
        shutil.copy(".env", dist_dir)
    elif Path(".env.example").exists():
        shutil.copy(".env.example", dist_dir / ".env")
    
    shutil.copy("requirements.txt", dist_dir)

    # 4. 优化 .env 配置 (针对打包环境)
    env_content = ""
    if Path(".env").exists():
        with open(".env", "r") as f:
            env_content = f.read()
    elif Path(".env.example").exists():
        with open(".env.example", "r") as f:
            env_content = f.read()
    
    # 修改 AMB_PATH 路径为相对于打包目录的路径
    new_lines = []
    for line in env_content.splitlines():
        if line.startswith("AMB_PATH="):
            new_lines.append(f"AMB_PATH={dist_dir.absolute()}/AutoMdxBuilder_python/AutoMdxBuilder")
        else:
            new_lines.append(line)
    
    with open(dist_dir / ".env", "w") as f:
        f.write("\n".join(new_lines))

    # 5. 处理 Redis
    print("准备 Redis 二进制文件...")
    bin_dir = dist_dir / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    if platform.system() == "Darwin":
        # Mac: 尝试复制本地 redis-server
        redis_path = subprocess.check_output(["which", "redis-server"]).decode().strip()
        if redis_path:
            shutil.copy(redis_path, bin_dir / "redis-server")
            print(f"✅ 已复制 Mac 版 Redis: {redis_path}")
    elif platform.system() == "Windows":
        print("⚠️ Windows 版 Redis 需要手动下载并放入 bin/redis-server.exe")
    
    # 4. 创建安装脚本 (针对小白)
    if platform.system() == "Darwin":
        with open(dist_dir / "一键启动.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write('cd "$(dirname "$0")"\n')
            f.write("if [ ! -d \"venv\" ]; then\n")
            f.write("  echo \"正在进行第一次运行初始化...\"\n")
            f.write("  python3 -m venv venv\n")
            f.write("  source venv/bin/activate\n")
            f.write("  pip install -r requirements.txt\n")
            f.write("fi\n")
            f.write("source venv/bin/activate\n")
            f.write("python desktop_launcher.py\n")
        os.chmod(dist_dir / "一键启动.sh", 0o755)
    
    print("\n=============================================")
    print(f"打包完成！请查看目录: {dist_dir.absolute()}")
    print("您可以将此目录整个压缩发送给朋友。")
    print("=============================================")

if __name__ == "__main__":
    pack()
