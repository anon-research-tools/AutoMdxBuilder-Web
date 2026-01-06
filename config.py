"""
Web应用配置文件
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.absolute()

# Flask配置
class Config:
    # 密钥（生产环境请修改）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 上传配置
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'static' / 'output'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB最大上传
    ALLOWED_EXTENSIONS = {'pdf'}

    # 文件清理配置（小时）
    FILE_RETENTION_HOURS = 24

    # Celery配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

    # AutoMdxBuilder路径
    AMB_PATH = os.environ.get('AMB_PATH') or '/usr/local/bin/AutoMdxBuilder'

    # PDF转换默认配置
    PDF_DEFAULT_DPI = 200
    PDF_DEFAULT_QUALITY = 75
    PDF_AUTO_CROP = False

    # 日志配置
    LOG_DIR = BASE_DIR / 'logs'

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.LOG_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
