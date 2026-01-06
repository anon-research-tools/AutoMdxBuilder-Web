"""
简化版 Flask 应用 - 无需 Celery 和 Redis
"""
from flask import Flask
from flask_cors import CORS
import logging
from pathlib import Path
import sys
import os

# 处理 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    REAL_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.absolute()
    REAL_DIR = BASE_DIR


class SimpleConfig:
    """简化配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # 使用实际目录（不是打包目录）
    UPLOAD_FOLDER = str(REAL_DIR / 'static' / 'uploads')
    OUTPUT_FOLDER = str(REAL_DIR / 'static' / 'output')
    LOG_DIR = str(REAL_DIR / 'logs')

    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'pdf'}

    PDF_DEFAULT_DPI = 300
    PDF_DEFAULT_QUALITY = 85
    PDF_AUTO_CROP = False


def create_app():
    """应用工厂函数"""
    app = Flask(__name__,
                template_folder=str(BASE_DIR / 'templates'),
                static_folder=str(REAL_DIR / 'static'))

    app.config.from_object(SimpleConfig)

    # 创建必要目录
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(app.config['LOG_DIR']).mkdir(parents=True, exist_ok=True)

    # 启用 CORS
    CORS(app)

    # 配置日志
    setup_logging(app)

    # 注册路由
    from app_simple.routes import bp
    app.register_blueprint(bp)

    app.logger.info('AutoMdxBuilder 简化版启动')

    return app


def setup_logging(app):
    """配置日志"""
    log_dir = Path(app.config['LOG_DIR'])
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(
        log_dir / 'app.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
