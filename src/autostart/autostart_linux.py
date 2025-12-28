"""
Linux autostart manager / Linux 开机自启管理器
"""
import sys
import os
from pathlib import Path

from ..utils.logger import logger


DESKTOP_ENTRY_TEMPLATE = """[Desktop Entry]
Type=Application
Name=Clash Env Cleaner
Name[zh_CN]=Clash 环境清理工具
Comment=Clean Clash proxy environment settings
Comment[zh_CN]=清理 Clash 代理环境设置
Exec={exec_path}
Icon=clash-env-cleaner
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


def get_autostart_dir() -> Path:
    """Get autostart directory / 获取自启动目录"""
    return Path.home() / ".config" / "autostart"


def get_desktop_file_path() -> Path:
    """Get desktop entry file path / 获取桌面条目文件路径"""
    return get_autostart_dir() / "clash-env-cleaner.desktop"


def get_app_path() -> str:
    """Get application executable path / 获取应用程序可执行文件路径"""
    if getattr(sys, 'frozen', False):
        # Running as compiled / 作为编译后的程序运行
        return sys.executable
    else:
        # Running as script / 作为脚本运行
        main_py = Path(__file__).parent.parent / "main.py"
        return f"{sys.executable} {main_py}"


def enable_autostart() -> bool:
    """Enable autostart on Linux / 启用 Linux 开机自启"""
    try:
        autostart_dir = get_autostart_dir()
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_file = get_desktop_file_path()
        exec_path = get_app_path()
        
        content = DESKTOP_ENTRY_TEMPLATE.format(exec_path=exec_path)
        desktop_file.write_text(content)
        
        # Make executable / 设为可执行
        desktop_file.chmod(0o755)
        
        logger.info("Linux autostart enabled")
        return True
    except Exception as e:
        logger.error(f"Failed to enable Linux autostart: {e}")
        return False


def disable_autostart() -> bool:
    """Disable autostart on Linux / 禁用 Linux 开机自启"""
    try:
        desktop_file = get_desktop_file_path()
        if desktop_file.exists():
            desktop_file.unlink()
        
        logger.info("Linux autostart disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable Linux autostart: {e}")
        return False


def is_autostart_enabled() -> bool:
    """Check if autostart is enabled on Linux / 检查 Linux 开机自启是否启用"""
    return get_desktop_file_path().exists()
