"""
Windows autostart manager / Windows 开机自启管理器
"""
import sys
import os
from pathlib import Path

from ..utils.logger import logger

def get_app_path() -> str:
    """Get application executable path / 获取应用程序可执行文件路径"""
    if getattr(sys, 'frozen', False):
        # Running as compiled / 作为编译后的程序运行
        return sys.executable
    else:
        # Running as script / 作为脚本运行
        main_py = str(Path(__file__).parent.parent / "main.py")
        return f'{sys.executable} "{main_py}"'

def enable_autostart() -> bool:
    """Enable autostart on Windows / 启用 Windows 开机自启"""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        
        app_path = get_app_path()
        winreg.SetValueEx(key, "ClashEnvCleaner", 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        
        logger.info("Windows autostart enabled")
        return True
    except Exception as e:
        logger.error(f"Failed to enable Windows autostart: {e}")
        return False

def disable_autostart() -> bool:
    """Disable autostart on Windows / 禁用 Windows 开机自启"""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        
        try:
            winreg.DeleteValue(key, "ClashEnvCleaner")
        except FileNotFoundError:
            pass  # Already disabled
        
        winreg.CloseKey(key)
        
        logger.info("Windows autostart disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable Windows autostart: {e}")
        return False

def is_autostart_enabled() -> bool:
    """Check if autostart is enabled on Windows / 检查 Windows 开机自启是否启用"""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        
        try:
            winreg.QueryValueEx(key, "ClashEnvCleaner")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception as e:
        logger.error(f"Failed to check Windows autostart status: {e}")
        return False
