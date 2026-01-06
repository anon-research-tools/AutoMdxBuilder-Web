import os
import subprocess
import time
import webbrowser
import sys
import signal
import platform
from pathlib import Path
from dotenv import load_dotenv
import threading

# 获取基础目录（处理 PyInstaller 打包后的路径）
if getattr(sys, 'frozen', False):
    # 打包环境
    BASE_DIR = Path(sys._MEIPASS)
    REAL_EXE_DIR = Path(sys.executable).parent
else:
    # 开发环境
    BASE_DIR = Path(__file__).parent.absolute()
    REAL_EXE_DIR = BASE_DIR

os.chdir(REAL_EXE_DIR)
SCRIPT_DIR = BASE_DIR

# 加载配置
load_dotenv(dotenv_path=REAL_EXE_DIR / ".env")

# 添加路径
sys.path.insert(0, str(BASE_DIR))

processes = []
is_shutting_down = False

def signal_handler(sig, frame):
    global is_shutting_down
    if is_shutting_down:
        return
    is_shutting_down = True
    
    print("\n正在关闭所有服务...")
    for p in processes:
        try:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                if p.poll() is None:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception as e:
            pass
    
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_redis():
    print("1. 检查 Redis 服务...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        if r.ping():
            print("✅ Redis 已经在运行")
            return True
    except:
        pass

    print("⚠️ Redis 未运行，尝试启动本地 Redis...")
    
    redis_cmd = "redis-server"
    if getattr(sys, 'frozen', False):
        bundled_redis = SCRIPT_DIR / "bin" / ("redis-server.exe" if platform.system() == "Windows" else "redis-server")
        if bundled_redis.exists():
            redis_cmd = str(bundled_redis)
    else:
        if platform.system() == "Windows":
            redis_path = SCRIPT_DIR / "bin" / "redis-server.exe"
            if redis_path.exists():
                redis_cmd = str(redis_path)

    try:
        p_kwargs = {}
        if platform.system() != "Windows":
            p_kwargs["preexec_fn"] = os.setsid
            
        p = subprocess.Popen([redis_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **p_kwargs)
        processes.append(p)
        time.sleep(2)
        print(f"✅ Redis 启动成功")
        return True
    except Exception as e:
        print(f"❌ 启动 Redis 失败: {e}")
        return False

def run_celery_worker():
    """在独立线程中运行 Celery Worker"""
    try:
        from app.tasks import celery_app
        argv = ['worker', '--loglevel=info', '--pool=solo']
        celery_app.worker_main(argv)
    except Exception as e:
        print(f"Celery Worker 错误: {e}")

def run_flask_app():
    """在独立线程中运行 Flask"""
    try:
        from app import create_app
        app = create_app(os.environ.get('FLASK_ENV', 'production'))
        app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask 错误: {e}")

def main():
    import multiprocessing
    multiprocessing.freeze_support()
    
    print("=============================================")
    print("AutoMdxBuilder - 桌面一键启动器")
    print("=============================================")
    
    # 创建必要目录
    (REAL_EXE_DIR / "static" / "uploads").mkdir(parents=True, exist_ok=True)
    (REAL_EXE_DIR / "static" / "output").mkdir(parents=True, exist_ok=True)
    (REAL_EXE_DIR / "logs").mkdir(parents=True, exist_ok=True)

    if not start_redis():
        input("按回车键退出...")
        return

    print("2. 启动异步任务后台 (Celery)...")
    celery_thread = threading.Thread(target=run_celery_worker, daemon=True)
    celery_thread.start()
    time.sleep(2)
    print("✅ Celery Worker 已启动")

    print("3. 启动 Web 服务 (Flask)...")
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    time.sleep(2)
    print("✅ Flask Web 服务已启动")

    print("\n🚀 所有服务已就绪！")
    print("🔗 访问地址: http://localhost:8000")
    print("💡 正在打开浏览器...")
    print("⚠️ 请不要关闭此窗口，关闭此窗口将停止服务。")
    print("=============================================")
    
    time.sleep(3)
    webbrowser.open("http://localhost:8000")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
