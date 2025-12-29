"""
Clash Environment Cleaner - Main Entry
Clash 环境清理工具 - 主入口
"""
import sys
import os

# Add src to path for relative imports / 将 src 添加到路径以支持相对导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.gui.main_window import MainWindow
from src.core.detector import clean_all_proxy
from src.utils.config import config
from src.utils.logger import logger
from src.utils.platform_utils import is_windows, is_linux

def setup_autostart():
    """Setup autostart based on config / 根据配置设置开机自启"""
    if is_windows():
        from src.autostart.autostart_windows import enable_autostart, is_autostart_enabled
    elif is_linux():
        from src.autostart.autostart_linux import enable_autostart, is_autostart_enabled
    else:
        return
    
    if config.get("auto_clean_on_startup") and not is_autostart_enabled():
        enable_autostart()
        logger.info("Autostart enabled / 开机自启已启用")

def auto_clean_on_startup():
    """Auto clean on startup if configured / 如果配置了则启动时自动清理"""
    if config.get("auto_clean_on_startup"):
        logger.info("Auto cleaning on startup / 启动时自动清理")
        report = clean_all_proxy()
        if report:
            logger.info(report.get_summary_en())

def main():
    """Main entry point / 主入口点"""
    logger.info("=" * 50)
    logger.info("Clash Environment Cleaner starting / Clash 环境清理工具启动")
    logger.info("=" * 50)
    
    # Setup autostart / 设置开机自启
    setup_autostart()
    
    # Auto clean on startup / 启动时自动清理
    auto_clean_on_startup()
    
    # Create Qt Application / 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray / 保持在托盘运行
    
    # Set application info / 设置应用信息
    app.setApplicationName("Clash Env Cleaner")
    app.setOrganizationName("ClashEnvCleaner")
    app.setApplicationVersion("1.0.0")
    
    # Create main window / 创建主窗口
    window = MainWindow()
    window.show()
    
    logger.info("Application ready / 应用就绪")
    
    # Run event loop / 运行事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
