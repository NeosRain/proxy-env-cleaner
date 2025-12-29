"""
Mirror source manager GUI using PyQt6 / 使用PyQt6的镜像源管理器GUI
Supports APT, NPM, Pip, Snap mirror configuration
支持 APT、NPM、Pip、Snap 镜像源配置
"""
import os
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from enum import Enum
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QTextEdit, QComboBox, QFrame,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ..core.mirror_manager import get_mirror_manager, MirrorProvider as CoreMirrorProvider, get_available_providers, MirrorManager
from ..utils.platform_utils import is_windows, is_linux, get_platform_name
import re

class DistroType(Enum):
    """Linux distribution type / Linux 发行版类型"""
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    UNKNOWN = "unknown"

class MirrorProvider(Enum):
    """Mirror provider / 镜像源提供商"""
    TSINGHUA = "tsinghua"       # 清华源
    ALIYUN = "aliyun"           # 阿里源
    USTC = "ustc"               # 中科大源
    HUAWEI = "huawei"           # 华为源
    TENCENT = "tencent"         # 腾讯源
    OFFICIAL = "official"       # 官方源

class ConfigWorker(QThread):
    """配置应用工作线程 / Config application worker thread"""
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, mirror_manager, apt_choice, npm_choice, pip_choice, snap_choice, yarn_choice):
        super().__init__()
        self.mirror_manager = mirror_manager
        self.apt_choice = apt_choice
        self.npm_choice = npm_choice
        self.pip_choice = pip_choice
        self.snap_choice = snap_choice
        self.yarn_choice = yarn_choice
    
    def run(self):
        try:
            results = {}
            
            # 根据选择映射到核心模块的MirrorProvider
            provider_map = {
                "清华源 / Tsinghua": CoreMirrorProvider.TSINGHUA,
                "阿里源 / Aliyun": CoreMirrorProvider.ALIYUN,
                "中科大源 / USTC": CoreMirrorProvider.USTC,
                "华为源 / Huawei": CoreMirrorProvider.HUAWEI,
                "腾讯源 / Tencent": CoreMirrorProvider.TENCENT,
                "淘宝源 / Taobao": CoreMirrorProvider.TSINGHUA,  # 使用清华源作为淘宝源的后端
            }
            
            # 处理APT配置 (仅Linux)
            if self.apt_choice != "不修改 / Keep current" and is_linux():
                if self.apt_choice.startswith("清华源"):
                    provider = CoreMirrorProvider.TSINGHUA
                elif self.apt_choice.startswith("阿里源"):
                    provider = CoreMirrorProvider.ALIYUN
                elif self.apt_choice.startswith("中科大源"):
                    provider = CoreMirrorProvider.USTC
                else:
                    provider = None
                
                if provider:
                    results["apt"] = self.mirror_manager.configure_apt_mirror(provider)
            
            # 处理NPM配置
            if self.npm_choice != "不修改 / Keep current":
                if self.npm_choice.startswith("淘宝源"):
                    provider = CoreMirrorProvider.TSINGHUA  # 淘宝源使用清华源作为后端
                elif self.npm_choice.startswith("清华源"):
                    provider = CoreMirrorProvider.TSINGHUA
                else:
                    provider = None
                
                if provider:
                    results["npm"] = self.mirror_manager.configure_npm_mirror(provider)
            
            # 处理Pip配置
            if self.pip_choice != "不修改 / Keep current":
                if self.pip_choice.startswith("清华源"):
                    provider = CoreMirrorProvider.TSINGHUA
                elif self.pip_choice.startswith("阿里源"):
                    provider = CoreMirrorProvider.ALIYUN
                elif self.pip_choice.startswith("中科大源"):
                    provider = CoreMirrorProvider.USTC
                else:
                    provider = None
                
                if provider:
                    results["pip"] = self.mirror_manager.configure_pip_mirror(provider)
            
            # 处理Yarn配置
            if self.yarn_choice != "不修改 / Keep current":
                if self.yarn_choice.startswith("淘宝源"):
                    provider = CoreMirrorProvider.TSINGHUA  # 淘宝源使用清华源作为后端
                else:
                    provider = None
                
                if provider:
                    results["yarn"] = self.mirror_manager.configure_yarn_mirror(provider)
            
            # 处理Snap配置 (仅Linux)
            if self.snap_choice != "不修改 / Keep current" and is_linux():
                if self.snap_choice.startswith("清华源"):
                    provider = CoreMirrorProvider.TSINGHUA
                elif self.snap_choice.startswith("中科大源"):
                    provider = CoreMirrorProvider.USTC
                else:
                    provider = None
                
                if provider:
                    results["snap"] = self.mirror_manager.configure_snap_mirror(provider)
            
            # 检查是否有任何配置被应用
            applied_configs = [k for k, v in results.items() if v]
            if applied_configs:
                success_msg = f"配置应用完成: {', '.join(applied_configs)} / Config applied: {', '.join(applied_configs)}"
                self.finished.emit(True, success_msg)
            else:
                self.finished.emit(True, "没有应用任何配置 / No configs applied")
                
        except Exception as e:
            self.finished.emit(False, f"❌ 配置失败: {str(e)} / Config failed: {str(e)}")

def show_mirror_settings(parent=None):
    """Show mirror settings dialog / 显示镜像设置对话框"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("镜像源管理 / Mirror Settings")
    dialog.resize(700, 600)
    
    # 创建镜像管理器实例 - 使用核心模块的管理器
    mirror_manager = get_mirror_manager()
    
    # 设置UI
    main_layout = QVBoxLayout(dialog)
    main_layout.setContentsMargins(10, 10, 10, 10)
    
    # 状态显示区域
    status_group = QGroupBox("状态信息 / Status Info")
    status_layout = QVBoxLayout(status_group)
    
    # 状态文本框
    status_text = QTextEdit()
    status_text.setMinimumHeight(150)
    status_layout.addWidget(status_text)
    
    # 刷新状态按钮
    def refresh_status():
        try:
            # 使用核心模块的检测方法
            info = mirror_manager.get_current_mirror_info()
            # 由于核心模块的detect_distro方法返回值格式不同，我们不直接使用
            platform_name = get_platform_name()
            
            status_lines = [
                "═══ 系统信息 / System Info ═══",
                f"   平台 / Platform: {platform_name}",
                "",
                "═══ 当前镜像源 / Current Mirrors ═══",
                f"   APT:   {info['apt']}",
                f"   NPM:   {info['npm']}",
                f"   Yarn:  {info['yarn']}",
                f"   Pip:   {info['pip']}",
                f"   Snap:  {info['snap']}",
            ]
            status_text.setPlainText("\n".join(status_lines))
        except Exception as e:
            error_msg = f"❌ 刷新状态失败 / Refresh failed: {str(e)}"
            status_text.setPlainText(error_msg)
    
    refresh_btn = QPushButton("🔄 刷新状态 / Refresh Status")
    refresh_btn.clicked.connect(refresh_status)
    status_layout.addWidget(refresh_btn)
    
    # 镜像源选择区域
    select_group = QGroupBox("选择镜像源 / Select Mirror")
    select_layout = QGridLayout(select_group)
    
    # APT 镜像源
    apt_label = QLabel("APT 源:")
    apt_combo = QComboBox()
    apt_combo.addItems(["不修改 / Keep current", "清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"])
    apt_combo.setCurrentText("不修改 / Keep current")
    select_layout.addWidget(apt_label, 0, 0)
    select_layout.addWidget(apt_combo, 0, 1)
    
    # NPM 镜像源
    npm_label = QLabel("NPM 源:")
    npm_combo = QComboBox()
    npm_combo.addItems(["不修改 / Keep current", "淘宝源 / Taobao"])
    npm_combo.setCurrentText("不修改 / Keep current")
    select_layout.addWidget(npm_label, 1, 0)
    select_layout.addWidget(npm_combo, 1, 1)
    
    # Pip 镜像源
    pip_label = QLabel("Pip 源:")
    pip_combo = QComboBox()
    pip_combo.addItems(["不修改 / Keep current", "清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"])
    pip_combo.setCurrentText("不修改 / Keep current")
    select_layout.addWidget(pip_label, 2, 0)
    select_layout.addWidget(pip_combo, 2, 1)
    
    # Snap 镜像源
    snap_label = QLabel("Snap 源:")
    snap_combo = QComboBox()
    snap_combo.addItems(["不修改 / Keep current", "清华源 / Tsinghua", "中科大源 / USTC"])
    snap_combo.setCurrentText("不修改 / Keep current")
    select_layout.addWidget(snap_label, 3, 0)
    select_layout.addWidget(snap_combo, 3, 1)
    
    # Yarn 镜像源
    yarn_label = QLabel("Yarn 源:")
    yarn_combo = QComboBox()
    yarn_combo.addItems(["不修改 / Keep current", "淘宝源 / Taobao"])
    yarn_combo.setCurrentText("不修改 / Keep current")
    select_layout.addWidget(yarn_label, 4, 0)
    select_layout.addWidget(yarn_combo, 4, 1)
    
    # 快速配置按钮
    quick_layout = QHBoxLayout()
    
    def quick_config(provider_name):
        # 根据选择的提供商设置所有下拉框
        if provider_name in ["清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"]:
            apt_combo.setCurrentText(provider_name)
            pip_combo.setCurrentText(provider_name)
            snap_combo.setCurrentText(provider_name)
        else:
            apt_combo.setCurrentText("不修改 / Keep current")
            pip_combo.setCurrentText("不修改 / Keep current")
            snap_combo.setCurrentText("不修改 / Keep current")
        
        if "淘宝" in provider_name:
            npm_combo.setCurrentText("淘宝源 / Taobao")
            yarn_combo.setCurrentText("淘宝源 / Taobao")
        else:
            npm_combo.setCurrentText("不修改 / Keep current")
            yarn_combo.setCurrentText("不修改 / Keep current")
    
    quick_1 = QPushButton("全部使用清华源")
    quick_1.clicked.connect(lambda: quick_config("清华源 / Tsinghua"))
    quick_layout.addWidget(quick_1)
    
    quick_2 = QPushButton("全部使用阿里源")
    quick_2.clicked.connect(lambda: quick_config("阿里源 / Aliyun"))
    quick_layout.addWidget(quick_2)
    
    quick_3 = QPushButton("全部使用中科大")
    quick_3.clicked.connect(lambda: quick_config("中科大源 / USTC"))
    quick_layout.addWidget(quick_3)
    
    select_layout.addLayout(quick_layout, 5, 0, 1, 2)
    
    # 应用配置按钮
    def apply_config():
        # 获取用户选择
        apt_choice = apt_combo.currentText()
        npm_choice = npm_combo.currentText()
        pip_choice = pip_combo.currentText()
        snap_choice = snap_combo.currentText()
        yarn_choice = yarn_combo.currentText()
        
        # 检查是否有选择任何配置
        if all(choice == "不修改 / Keep current" for choice in [apt_choice, npm_choice, pip_choice, snap_choice, yarn_choice]):
            msg = QMessageBox(parent)
            msg.setWindowTitle("警告 / Warning")
            msg.setText("未选择任何镜像源 / No mirror selected")
            msg.exec()
            return
        
        # 确认对话框
        confirm = QMessageBox(parent)
        confirm.setWindowTitle("确认 / Confirm")
        confirm.setText("将备份当前配置并应用新镜像源。\nThis will backup current config and apply new mirrors.\n\n继续？/Continue?")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            # 使用工作线程执行配置应用
            worker = ConfigWorker(mirror_manager, apt_choice, npm_choice, pip_choice, snap_choice, yarn_choice)
            
            def on_finished(success, message):
                if success:
                    msg = QMessageBox(parent)
                    msg.setWindowTitle("完成 / Completed")
                    msg.setText(message)
                    msg.exec()
                else:
                    msg = QMessageBox(parent)
                    msg.setWindowTitle("错误 / Error")
                    msg.setText(message)
                    msg.exec()
                
                refresh_status()
            
            worker.finished.connect(on_finished)
            worker.start()
    
    apply_btn = QPushButton("应用配置 / Apply Config")
    apply_btn.clicked.connect(apply_config)
    
    # 日志区域
    log_group = QGroupBox("操作日志 / Operation Log")
    log_layout = QVBoxLayout(log_group)
    
    log_text = QTextEdit()
    log_text.setMinimumHeight(150)
    log_layout.addWidget(log_text)
    
    # 添加所有组件到主布局
    main_layout.addWidget(status_group)
    main_layout.addWidget(select_group)
    main_layout.addWidget(apply_btn)
    main_layout.addWidget(log_group)
    
    # 刷新初始状态
    refresh_status()
    
    # 显示对话框
    dialog.exec()

if __name__ == "__main__":
    # 测试用
    app = QApplication([])
    show_mirror_settings()
    app.exec()
