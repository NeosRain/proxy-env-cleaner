"""
System tray icon / 系统托盘图标
"""
import sys
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtCore import QObject, pyqtSignal

from ..core.detector import clean_all_proxy
from ..core.cleaner_base import CleanReport
from ..utils.logger import logger

class TrayIcon(QObject):
    """System tray icon manager / 系统托盘图标管理器"""
    
    # Signals / 信号
    clean_completed = pyqtSignal(object)  # CleanReport
    quit_requested = pyqtSignal()
    show_window_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.menu: Optional[QMenu] = None
        self._setup_tray()
    
    def _create_default_icon(self) -> QIcon:
        """Create default icon / 创建默认图标"""
        # Create a simple colored icon / 创建简单的彩色图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a broom icon (simplified) / 绘制扫帚图标（简化）
        painter.setBrush(QBrush(QColor(52, 152, 219)))  # Blue
        painter.setPen(QColor(41, 128, 185))
        painter.drawEllipse(8, 8, 48, 48)
        
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), 0x0084, "P")  # Center aligned "P" for Proxy
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _setup_tray(self) -> None:
        """Setup system tray / 设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self._create_default_icon())
        
        # Create context menu / 创建右键菜单
        self.menu = QMenu()
        
        # Show window action / 显示窗口动作
        show_action = QAction("显示主窗口 / Show Window", self.menu)
        show_action.triggered.connect(self._on_show_window)
        self.menu.addAction(show_action)
        
        self.menu.addSeparator()
        
        # One-click clean action / 一键清理动作
        clean_action = QAction("一键清理 / Quick Clean", self.menu)
        clean_action.triggered.connect(self._on_quick_clean)
        self.menu.addAction(clean_action)
        
        # Clean and exit action / 清理后退出动作
        clean_exit_action = QAction("清理后退出 / Clean & Exit", self.menu)
        clean_exit_action.triggered.connect(self._on_clean_and_exit)
        self.menu.addAction(clean_exit_action)
        
        self.menu.addSeparator()
        
        # Exit action / 退出动作
        exit_action = QAction("退出 / Exit", self.menu)
        exit_action.triggered.connect(self._on_exit)
        self.menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.menu)
        
        # Double-click to show window / 双击显示窗口
        self.tray_icon.activated.connect(self._on_activated)
        
        # Set tooltip / 设置工具提示
        self.tray_icon.setToolTip("代理环境清理工具 / Proxy Env Cleaner")
    
    def show(self) -> None:
        """Show tray icon / 显示托盘图标"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self) -> None:
        """Hide tray icon / 隐藏托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show_message(self, title: str, message: str, 
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """Show tray notification / 显示托盘通知"""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, 3000)
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation / 处理托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
    
    def _on_show_window(self) -> None:
        """Show main window / 显示主窗口"""
        self.show_window_requested.emit()
    
    def _on_quick_clean(self) -> None:
        """Quick clean / 一键清理"""
        logger.info("Quick clean triggered from tray")
        self.show_message(
            "正在清理... / Cleaning...",
            "正在清理代理环境设置...\nCleaning proxy environment settings..."
        )
        
        report = clean_all_proxy()
        if report:
            self.clean_completed.emit(report)
            self.show_message(
                "清理完成 / Clean Completed",
                report.get_summary()
            )
        else:
            self.show_message(
                "清理失败 / Clean Failed",
                "不支持的平台\nUnsupported platform",
                QSystemTrayIcon.MessageIcon.Warning
            )
    
    def _on_clean_and_exit(self) -> None:
        """Clean and exit / 清理后退出"""
        logger.info("Clean and exit triggered from tray")
        self.show_message(
            "正在清理... / Cleaning...",
            "清理完成后将自动退出...\nWill exit after cleaning..."
        )
        
        report = clean_all_proxy()
        if report:
            self.clean_completed.emit(report)
            logger.info(f"Clean completed: {report.get_summary_en()}")
        
        # Exit application / 退出应用
        self.quit_requested.emit()
    
    def _on_exit(self) -> None:
        """Exit application / 退出应用"""
        self.quit_requested.emit()
