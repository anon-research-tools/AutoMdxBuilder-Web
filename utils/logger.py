"""
统一日志系统
提供全局日志记录功能
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class AppLogger:
    """应用程序日志管理器"""

    _instance = None
    _logger = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志系统"""
        if self._logger is not None:
            return

        self._logger = logging.getLogger('AutoMdxBuilder_GUI')
        self._logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if self._logger.handlers:
            return

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # 文件处理器（可选）
        try:
            log_dir = Path.home() / '.automdxbuilder' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
        except Exception as e:
            self._logger.warning(f"无法创建日志文件: {e}")

    @classmethod
    def get_logger(cls):
        """
        获取日志记录器

        Returns:
            logging.Logger: 日志记录器实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance._logger


def get_logger():
    """
    便捷函数：获取应用日志记录器

    Returns:
        logging.Logger: 日志记录器实例

    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger()
        >>> logger.info("应用启动")
        >>> logger.error("发生错误", exc_info=True)
    """
    return AppLogger.get_logger()
