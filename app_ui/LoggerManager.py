from loguru import logger
from typing import Callable
import os

class LoggerManager:
    """日志管理器，负责日志初始化和多通道输出"""
    def __init__(self, log_file: str, gui_log_func: Callable[[str], None] = None):
        """
        初始化日志管理器
        Args:
            log_file: 日志文件路径
            gui_log_func: GUI 日志输出函数
        """
        logger.remove()
        if gui_log_func:
            logger.add(gui_log_func, format="{message}")
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        logger.add(log_file, rotation="1 MB")

    @staticmethod
    def get_logger():
        """获取 loguru logger 实例"""
        return logger 