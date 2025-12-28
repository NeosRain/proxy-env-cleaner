"""
Logger utility / 日志工具
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from .platform_utils import is_windows


def get_log_dir() -> Path:
    """Get log directory / 获取日志目录"""
    if is_windows():
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    
    log_dir = base / "ClashEnvCleaner" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name: str = "ClashEnvCleaner") -> logging.Logger:
    """Setup and return logger / 设置并返回日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Console handler / 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    
    # File handler / 文件处理器
    log_file = get_log_dir() / f"cleaner_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers if not already added / 添加处理器（如果尚未添加）
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance / 全局日志实例
logger = setup_logger()
