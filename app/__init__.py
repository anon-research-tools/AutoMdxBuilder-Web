"""
Flask应用初始化
"""
from flask import Flask
from flask_cors import CORS
from config import config
import logging
from pathlib import Path


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 启用CORS
    CORS(app)

    # 配置日志
    setup_logging(app)

    # 注册蓝图
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    app.logger.info('AutoMdxBuilder Web应用启动')

    return app


def setup_logging(app):
    """配置日志"""
    log_dir = Path(app.config['LOG_DIR'])
    log_dir.mkdir(parents=True, exist_ok=True)

    # 文件处理器
    file_handler = logging.FileHandler(
        log_dir / 'app.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # 添加处理器
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
