"""
Platform utilities / 平台工具
"""
import platform
import sys


def is_windows() -> bool:
    """Check if running on Windows / 检查是否为 Windows 系统"""
    return platform.system() == "Windows"


def is_linux() -> bool:
    """Check if running on Linux / 检查是否为 Linux 系统"""
    return platform.system() == "Linux"


def get_platform_name() -> str:
    """Get platform name / 获取平台名称"""
    return platform.system()


def require_admin() -> bool:
    """Check if admin privileges are required / 检查是否需要管理员权限"""
    if is_windows():
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    elif is_linux():
        import os
        return os.geteuid() == 0
    return False
