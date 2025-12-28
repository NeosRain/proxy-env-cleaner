"""
Environment detector and cleaner factory / 环境检测器和清理器工厂
"""
from typing import Optional

from .cleaner_base import BaseCleaner, CleanReport, DetectResult
from ..utils.platform_utils import is_windows, is_linux
from ..utils.logger import logger


def get_cleaner() -> Optional[BaseCleaner]:
    """Get platform-specific cleaner / 获取平台特定的清理器"""
    if is_windows():
        from .cleaner_windows import WindowsCleaner
        return WindowsCleaner()
    elif is_linux():
        from .cleaner_linux import LinuxCleaner
        return LinuxCleaner()
    else:
        logger.error(f"Unsupported platform")
        return None


def detect_proxy_settings() -> list:
    """Detect all proxy settings / 检测所有代理设置"""
    cleaner = get_cleaner()
    if cleaner:
        return cleaner.detect_all()
    return []


def clean_all_proxy() -> Optional[CleanReport]:
    """Clean all proxy settings / 清理所有代理设置"""
    cleaner = get_cleaner()
    if cleaner:
        return cleaner.clean_all()
    return None
