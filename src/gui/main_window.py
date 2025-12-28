"""
Main window / 主窗口
"""
import sys
from typing import Optional, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox,
    QCheckBox, QMessageBox, QApplication, QFrame
)
from PyQt6.QtGui import QFont, QCloseEvent
from PyQt6.QtCore import Qt, QTimer

from .tray_icon import TrayIcon
from .mirror_dialog import show_mirror_settings
from ..core.detector import detect_proxy_settings, clean_all_proxy, get_cleaner
from ..core.cleaner_base import CleanReport, DetectResult, CleanStatus
from ..utils.config import config
from ..utils.logger import logger


class MainWindow(QMainWindow):
    """Main application window / 主应用窗口"""
    
    def __init__(self):
        super().__init__()
        self.tray: Optional[TrayIcon] = None
        self._init_ui()
        self._setup_tray()
        self._connect_signals()
        
        # Auto detect on startup / 启动时自动检测
        QTimer.singleShot(500, self._refresh_status)
    
    def _init_ui(self) -> None:
        """Initialize UI / 初始化界面"""
        self.setWindowTitle("代理环境清理工具 / Proxy Env Cleaner")
        self.setMinimumSize(550, 450)
        self.resize(600, 480)
        
        # Central widget / 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout / 主布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title / 标题
        title_label = QLabel("代理环境清理工具\nProxy Environment Cleaner")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Status group / 状态分组
        status_group = QGroupBox("环境状态检测 / Environment Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(100)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        status_layout.addWidget(self.status_text)
        
        # Refresh button / 刷新按钮
        refresh_btn = QPushButton("刷新状态 / Refresh Status")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 15px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #5d6d7e;
                padding-top: 8px;
                padding-bottom: 4px;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        # Options group / 选项分组
        options_group = QGroupBox("清理选项 / Clean Options")
        options_layout = QVBoxLayout(options_group)
        
        self.opt_system_proxy = QCheckBox("系统代理设置 / System Proxy Settings")
        self.opt_system_proxy.setChecked(config.get("clean_system_proxy"))
        
        self.opt_env_vars = QCheckBox("环境变量 / Environment Variables")
        self.opt_env_vars.setChecked(config.get("clean_env_variables"))
        
        self.opt_git_proxy = QCheckBox("Git 代理配置 / Git Proxy Config")
        self.opt_git_proxy.setChecked(config.get("clean_git_proxy"))
        
        options_layout.addWidget(self.opt_system_proxy)
        options_layout.addWidget(self.opt_env_vars)
        options_layout.addWidget(self.opt_git_proxy)
        
        layout.addWidget(options_group)
        
        # Buttons / 按钮
        btn_layout = QHBoxLayout()
        
        self.clean_btn = QPushButton("一键清理 / Quick Clean")
        self.clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5985;
                padding-top: 12px;
                padding-bottom: 8px;
            }
        """)
        self.clean_btn.clicked.connect(self._on_clean)
        btn_layout.addWidget(self.clean_btn)
        
        self.clean_exit_btn = QPushButton("清理后退出 / Clean & Exit")
        self.clean_exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #922b21;
                padding-top: 12px;
                padding-bottom: 8px;
            }
        """)
        self.clean_exit_btn.clicked.connect(self._on_clean_and_exit)
        btn_layout.addWidget(self.clean_exit_btn)
        
        layout.addLayout(btn_layout)
        
        # Mirror settings button / 镜像源设置按钮
        mirror_btn = QPushButton("镜像源管理 / Mirror Settings")
        mirror_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #6c3483;
                padding-top: 12px;
                padding-bottom: 8px;
            }
        """)
        mirror_btn.clicked.connect(self._open_mirror_settings)
        layout.addWidget(mirror_btn)
        
        # Log group / 日志分组
        log_group = QGroupBox("操作日志 / Operation Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Set stretch / 设置伸缩
        layout.setStretch(0, 0)  # Title
        layout.setStretch(1, 1)  # Status
        layout.setStretch(2, 0)  # Options
        layout.setStretch(3, 0)  # Buttons
        layout.setStretch(4, 2)  # Log
    
    def _setup_tray(self) -> None:
        """Setup system tray / 设置系统托盘"""
        self.tray = TrayIcon(self)
        self.tray.show()
    
    def _connect_signals(self) -> None:
        """Connect signals / 连接信号"""
        if self.tray:
            self.tray.show_window_requested.connect(self._show_window)
            self.tray.quit_requested.connect(self._quit_app)
            self.tray.clean_completed.connect(self._on_clean_completed)
    
    def _show_window(self) -> None:
        """Show and activate window / 显示并激活窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def _quit_app(self) -> None:
        """Quit application / 退出应用"""
        if self.tray:
            self.tray.hide()
        QApplication.quit()
    
    def _open_mirror_settings(self) -> None:
        """打开镜像源设置对话框 / Open mirror settings dialog"""
        try:
            show_mirror_settings(self)
        except Exception as e:
            QMessageBox.critical(self, "错误 / Error", f"打开镜像源管理器失败:\nFailed to open mirror manager:\n{str(e)}")
            logger.error(f"Failed to open mirror settings: {e}")
    
    def _refresh_status(self) -> None:
        """Refresh proxy status / 刷新代理状态"""
        self._log("正在检测环境... / Detecting environment...")
        
        results = detect_proxy_settings()
        
        self.status_text.clear()
        
        found_any = False
        for result in results:
            if result.found:
                found_any = True
                self.status_text.append(f"⚠️ {result.message_zh}")
                self.status_text.append(f"   {result.message_en}")
                self.status_text.append("")
        
        if not found_any:
            self.status_text.append("✅ 未检测到代理设置")
            self.status_text.append("   No proxy settings detected")
        
        self._log("检测完成 / Detection completed")
    
    def _on_clean(self) -> None:
        """Handle clean button click / 处理清理按钮点击"""
        self._log("开始清理... / Starting clean...")
        
        report = clean_all_proxy()
        if report:
            self._on_clean_completed(report)
        else:
            self._log("❌ 清理失败: 不支持的平台 / Clean failed: Unsupported platform")
    
    def _on_clean_and_exit(self) -> None:
        """Handle clean and exit button click / 处理清理后退出按钮点击"""
        self._on_clean()
        QTimer.singleShot(1000, self._quit_app)
    
    def _on_clean_completed(self, report: CleanReport) -> None:
        """Handle clean completed / 处理清理完成"""
        self._log("=" * 50)
        self._log("清理报告 / Clean Report:")
        self._log("-" * 50)
        
        for result in report.results:
            status_icon = {
                CleanStatus.SUCCESS: "✅",
                CleanStatus.FAILED: "❌",
                CleanStatus.SKIPPED: "⏭️",
                CleanStatus.NOT_FOUND: "ℹ️"
            }.get(result.status, "❓")
            
            self._log(f"{status_icon} {result.message_zh}")
            self._log(f"   {result.message_en}")
        
        self._log("-" * 50)
        self._log(report.get_summary_zh())
        self._log(report.get_summary_en())
        self._log("=" * 50)
        
        # Refresh status after clean / 清理后刷新状态
        QTimer.singleShot(500, self._refresh_status)
        
        # Show notification / 显示通知
        if self.tray:
            self.tray.show_message(
                "清理完成 / Clean Completed",
                report.get_summary()
            )
    
    def _log(self, message: str) -> None:
        """Append message to log / 追加消息到日志"""
        self.log_text.append(message)
        # Scroll to bottom / 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event / 处理窗口关闭事件"""
        if config.get("minimize_to_tray"):
            event.ignore()
            self.hide()
            if self.tray:
                self.tray.show_message(
                    "最小化到托盘 / Minimized to Tray",
                    "程序已最小化到系统托盘\nApplication minimized to system tray"
                )
        else:
            self._quit_app()
