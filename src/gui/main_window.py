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
from ..core.mirror_manager import get_mirror_manager, MirrorProvider, fetch_local_mirrors
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
        
        # Apply system theme adaptive styling
        self._apply_theme_styling()
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
        
        # Speed test button / 测速按钮
        speed_test_btn = QPushButton("镜像源测速 / Mirror Speed Test")
        speed_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
                padding-top: 12px;
                padding-bottom: 8px;
            }
        """)
        speed_test_btn.clicked.connect(self._test_mirror_speeds)
        layout.addWidget(speed_test_btn)
        
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
    
    def _apply_theme_styling(self) -> None:
        """Apply system theme adaptive styling / 应用系统主题自适应样式"""
        # 根据系统主题自动调整文本框样式
        try:
            from PyQt6.QtWidgets import QStyleFactory
            from PyQt6.QtGui import QPalette
            
            # 获取系统调色板
            palette = self.palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            text_color = palette.color(QPalette.ColorRole.WindowText)
            
            # 计算亮度，判断是否为深色主题
            brightness = (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000
            
            if brightness < 128:  # 深色主题
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
            else:  # 浅色主题
                self.status_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 10px;
                        font-family: Consolas, Monaco, monospace;
                    }
                """)
        except Exception as e:
            # 如果无法获取系统主题，使用默认深色主题
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
            import traceback
            print(f"Theme styling error: {e}\n{traceback.format_exc()}")
    
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
                # 显示更详细的信息，明确指出哪个应用被代理以及清理了什么环境
                if result.item == "system_proxy":
                    self.status_text.append(f"⚠️ [系统代理] {result.message_zh}")
                    self.status_text.append(f"   [System Proxy] {result.message_en}")
                elif result.item.startswith("env_"):
                    var_name = result.item[4:]
                    self.status_text.append(f"⚠️ [环境变量] {result.message_zh}")
                    self.status_text.append(f"   [Environment Variable] {result.message_en}")
                elif result.item == "git_proxy":
                    self.status_text.append(f"⚠️ [Git配置] {result.message_zh}")
                    self.status_text.append(f"   [Git Config] {result.message_en}")
                elif result.item == "npm_proxy":
                    self.status_text.append(f"⚠️ [NPM配置] {result.message_zh}")
                    self.status_text.append(f"   [NPM Config] {result.message_en}")
                elif result.item == "yarn_proxy":
                    self.status_text.append(f"⚠️ [Yarn配置] {result.message_zh}")
                    self.status_text.append(f"   [Yarn Config] {result.message_en}")
                elif result.item == "pip_proxy":
                    self.status_text.append(f"⚠️ [Pip配置] {result.message_zh}")
                    self.status_text.append(f"   [Pip Config] {result.message_en}")
                elif result.item == "apt_proxy":
                    self.status_text.append(f"⚠️ [APT源] {result.message_zh}")
                    self.status_text.append(f"   [APT Source] {result.message_en}")
                elif result.item == "uwp_loopback":
                    self.status_text.append(f"⚠️ [UWP回环] {result.message_zh}")
                    self.status_text.append(f"   [UWP Loopback] {result.message_en}")
                elif result.item == "kde_apps_proxy":
                    self.status_text.append(f"⚠️ [KDE应用] {result.message_zh}")
                    self.status_text.append(f"   [KDE Apps] {result.message_en}")
                elif result.item == "sources_proxy":
                    self.status_text.append(f"⚠️ [软件源] {result.message_zh}")
                    self.status_text.append(f"   [Software Sources] {result.message_en}")
                elif result.item == "wget_proxy":
                    self.status_text.append(f"⚠️ [Wget配置] {result.message_zh}")
                    self.status_text.append(f"   [Wget Config] {result.message_en}")
                elif result.item == "curl_proxy":
                    self.status_text.append(f"⚠️ [Curl配置] {result.message_zh}")
                    self.status_text.append(f"   [Curl Config] {result.message_en}")
                else:
                    self.status_text.append(f"⚠️ [{result.item}] {result.message_zh}")
                    self.status_text.append(f"   [{result.item}] {result.message_en}")
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
    
    def _test_mirror_speeds(self) -> None:
        """测试所有镜像源速度 / Test all mirror speeds"""
        try:
            from PyQt6.QtWidgets import QProgressDialog
            from PyQt6.QtCore import QThread, pyqtSignal
            
            # 创建进度对话框
            progress = QProgressDialog("正在测试镜像源速度...", "取消", 0, 100, self)
            progress.setWindowTitle("测速中...")
            progress.setCancelButton(None)  # 暂时不允许取消，因为测速过程复杂
            progress.show()
            
            self._log("开始测试镜像源速度... / Testing mirror speeds...")
            
            # 获取镜像管理器并测试所有镜像源
            mirror_manager = get_mirror_manager()
            results = mirror_manager.test_all_mirrors_speed()
            
            # 显示结果
            self.status_text.clear()
            self.status_text.append("镜像源测速结果 / Mirror Speed Test Results")
            self.status_text.append("=" * 50)
            
            # 按延迟时间排序结果
            sorted_results = {}
            for provider, provider_results in results.items():
                # 计算平均延迟时间
                total_latency = 0
                count = 0
                for url_type, (success, latency, error) in provider_results.items():
                    if success:
                        total_latency += latency
                        count += 1
                
                avg_latency = total_latency / count if count > 0 else float('inf')
                sorted_results[provider] = (avg_latency, provider_results)
            
            # 按平均延迟排序
            sorted_providers = sorted(sorted_results.items(), key=lambda x: x[1][0])
            
            for provider, (avg_latency, provider_results) in sorted_providers:
                # 从MirrorProvider枚举获取配置信息
                from ..core.mirror_manager import MIRROR_PROVIDERS
                config = MIRROR_PROVIDERS[provider]
                self.status_text.append(f"\n【{config.name_zh} - {config.name}】")
                
                if avg_latency == float('inf'):
                    self.status_text.append("  ❌ 无法连接 / Cannot connect")
                else:
                    self.status_text.append(f"  📊 平均延迟 / Avg latency: {avg_latency:.3f}s ({avg_latency*1000:.1f}ms)")
                
                for url_type, (success, latency, error) in provider_results.items():
                    if success:
                        self.status_text.append(f"    ✅ {url_type}: {latency:.3f}s ({latency*1000:.1f}ms)")
                    else:
                        self.status_text.append(f"    ❌ {url_type}: Error - {error}")
                
                self.status_text.append("-" * 30)
            
            self._log("镜像源测速完成 / Mirror speed test completed")
            progress.close()
            
        except Exception as e:
            self._log(f"❌ 测速失败: {str(e)} / Speed test failed: {str(e)}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误 / Error", f"测速失败:\nSpeed test failed:\n{str(e)}")
    
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
