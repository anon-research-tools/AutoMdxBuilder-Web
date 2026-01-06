#!/usr/bin/env python3
"""
AutoMdxBuilder 简化版桌面启动器
无需 Redis 和 Celery，真正一键启动！
"""
import os
import sys
import time
import webbrowser
import signal
import platform
from pathlib import Path


def get_base_paths():
    """获取基础路径（兼容打包和开发环境）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包环境
        base_dir = Path(sys._MEIPASS)
        real_dir = Path(sys.executable).parent
    else:
        # 开发环境
        base_dir = Path(__file__).parent.absolute()
        real_dir = base_dir
    return base_dir, real_dir


def setup_environment():
    """设置环境"""
    base_dir, real_dir = get_base_paths()

    # 切换到实际目录
    os.chdir(real_dir)

    # 添加路径
    sys.path.insert(0, str(base_dir))

    # 创建必要目录
    (real_dir / "static" / "uploads").mkdir(parents=True, exist_ok=True)
    (real_dir / "static" / "output").mkdir(parents=True, exist_ok=True)
    (real_dir / "logs").mkdir(parents=True, exist_ok=True)

    return base_dir, real_dir


def run_flask_app(port=8000):
    """运行 Flask 应用"""
    from app_simple import create_app

    app = create_app()

    # 禁用 Flask 的默认启动信息
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)


def open_browser_delayed(port, delay=2):
    """延迟打开浏览器"""
    import threading

    def _open():
        time.sleep(delay)
        webbrowser.open(f"http://localhost:{port}")

    t = threading.Thread(target=_open, daemon=True)
    t.start()


def signal_handler(sig, frame):
    """处理退出信号"""
    print("\n正在关闭服务...")
    os._exit(0)


def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 设置环境
    base_dir, real_dir = setup_environment()

    port = 8000

    print("=" * 50)
    print("  AutoMdxBuilder - 电子词典制作工具")
    print("=" * 50)
    print()
    print(f"  工作目录: {real_dir}")
    print(f"  访问地址: http://localhost:{port}")
    print()
    print("  正在启动服务，请稍候...")
    print()
    print("  提示：关闭此窗口将停止服务")
    print("=" * 50)

    # 延迟打开浏览器
    open_browser_delayed(port, delay=2)

    # 启动 Flask（阻塞）
    try:
        run_flask_app(port)
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n按回车键退出...")
        input()


if __name__ == "__main__":
    main()
