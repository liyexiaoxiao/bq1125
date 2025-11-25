import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    def __init__(self, log_dir='', max_bytes=5 * 1024 * 1024, backup_count=5):
        """
        初始化日志模块。

        :param log_dir: 日志文件存储目录
        :param max_bytes: 单个日志文件的最大字节数，默认 5MB
        :param backup_count: 备份文件数量
        """
        # 获取当前目录
        current_directory = os.getcwd()
        # 日志目录
        log_dir = current_directory + "\\logs\\"
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)

        # 获取当前时间戳，用于命名日志文件
        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

        # 创建日志文件路径
        self.all_log_file = os.path.join(log_dir, f"log_{timestamp}.log")
        self.error_log_file = os.path.join(log_dir, f"log_{timestamp}_err.log")
        self.warn_log_file = os.path.join(log_dir, f"log_{timestamp}_warn.log")

        # 配置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # 配置主日志记录器（记录所有日志）
        self.logger = logging.getLogger("main_logger")
        self.logger.setLevel(logging.DEBUG)

        # 配置主日志处理器（RotatingFileHandler，限制文件大小）
        all_handler = RotatingFileHandler(self.all_log_file, maxBytes=max_bytes, backupCount=backup_count)
        all_handler.setFormatter(formatter)
        self.logger.addHandler(all_handler)

        # 配置错误日志记录器
        self.error_logger = logging.getLogger("error_logger")
        self.error_logger.setLevel(logging.ERROR)
        error_handler = RotatingFileHandler(self.error_log_file, maxBytes=max_bytes, backupCount=backup_count)
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)

        # 配置警告日志记录器
        self.warn_logger = logging.getLogger("warn_logger")
        self.warn_logger.setLevel(logging.WARNING)
        warn_handler = RotatingFileHandler(self.warn_log_file, maxBytes=max_bytes, backupCount=backup_count)
        warn_handler.setFormatter(formatter)
        self.warn_logger.addHandler(warn_handler)

    def info(self, message):
        """记录 Info 类型日志"""
        self.logger.info(message)

    def error(self, message):
        """记录 Error 类型日志"""
        self.logger.error(message)
        self.error_logger.error(message)

    def warn(self, message):
        """记录 Warn 类型日志"""
        self.logger.warning(message)
        self.warn_logger.warning(message)

    def debug(self, message):
        """记录 Debug 类型日志"""
        self.logger.debug(message)