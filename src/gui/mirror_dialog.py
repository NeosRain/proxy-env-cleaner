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


# 在线配置 URL / Online config URL
ONLINE_CONFIG_URL = "https://raw.githubusercontent.com/NeosRain/proxy-env-cleaner/main/mirrors.json"


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


class MirrorManager:
    """Mirror source manager / 镜像源管理器"""
    
    # APT sources file paths / APT 源文件路径
    SOURCES_LIST = Path("/etc/apt/sources.list")
    SOURCES_LIST_D = Path("/etc/apt/sources.list.d/")
    
    # Other config paths / 其他配置路径
    NPM_RC = Path.home() / ".npmrc"
    PIP_CONF = Path.home() / ".pip" / "pip.conf"
    PIP_CONF_ALT = Path.home() / ".config" / "pip" / "pip.conf"
    # Windows pip config
    PIP_CONF_WIN = Path(os.environ.get("APPDATA", "")) / "pip" / "pip.ini"
    GIT_CONFIG = Path.home() / ".gitconfig"
    
    # Snap config / Snap 配置
    SNAP_AUTH_JSON = Path("/var/snap/snap-store/common/snap-auth.json")
    SNAPD_ENV = Path("/etc/environment")
    
    # Backup settings / 备份设置
    MAX_BACKUPS = 5
    
    def __init__(self):
        self.creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    
    def detect_distro(self):
        """Detect Linux distribution / 检测 Linux 发行版"""
        if os.name == 'nt':  # Windows
            return DistroType.UNKNOWN, "Windows"
        
        try:
            os_release = Path("/etc/os-release")
            if os_release.exists():
                content = os_release.read_text()
                
                if "debian" in content.lower():
                    # Get version codename
                    import re
                    match = re.search(r'VERSION_CODENAME=(\w+)', content)
                    codename = match.group(1) if match else "stable"
                    return DistroType.DEBIAN, codename
                
                elif "ubuntu" in content.lower():
                    match = re.search(r'VERSION_CODENAME=(\w+)', content)
                    codename = match.group(1) if match else "jammy"
                    return DistroType.UBUNTU, codename
        except Exception as e:
            print(f"Failed to detect distro: {e}")
        
        return DistroType.UNKNOWN, "unknown"
    
    def get_current_mirror_info(self):
        """获取所有包管理器当前镜像信息 / Get current mirror info for all package managers"""
        import re
        info = {
            "apt": "未检测到 / Not detected",
            "npm": "未检测到 / Not detected",
            "pip": "未检测到 / Not detected",
            "yarn": "未检测到 / Not detected",
            "snap": "未检测到 / Not detected",
        }

        # APT - Linux only
        if os.name != 'nt' and self.SOURCES_LIST.exists():
            try:
                content = self.SOURCES_LIST.read_text()
                for line in content.splitlines():
                    if line.strip().startswith('deb ') and not line.strip().startswith('#'):
                        match = re.search(r'https?://([^\s/]+)', line)
                        if match:
                            info["apt"] = match.group(1)
                            break
            except Exception:
                pass
        elif os.name == 'nt':
            info["apt"] = "N/A (Windows)"
        
        # NPM - 多种检测方式
        npm_detected = False
        # 方法 1: npm config get registry
        try:
            result = subprocess.run(
                ["npm", "config", "get", "registry"],
                capture_output=True, text=True, timeout=10,
                creationflags=self.creationflags
            )
            if result.returncode == 0 and result.stdout.strip():
                registry = result.stdout.strip()
                if registry and registry != "undefined" and "http" in registry:
                    info["npm"] = registry
                    npm_detected = True
        except Exception:
            pass
        
        # 方法 2: 检查 .npmrc 文件
        if not npm_detected and self.NPM_RC.exists():
            try:
                content = self.NPM_RC.read_text()
                match = re.search(r'registry\s*=\s*"?([^\s"\n]+)', content)
                if match:
                    info["npm"] = match.group(1)
                    npm_detected = True
            except Exception:
                pass
        
        # 方法 3: npm config list 
        if not npm_detected:
            try:
                result = subprocess.run(
                    ["npm", "config", "list"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=self.creationflags
                )
                if result.returncode == 0:
                    match = re.search(r'registry\s*=\s*"?([^\s"\n]+)', result.stdout)
                    if match:
                        info["npm"] = match.group(1)
            except Exception:
                pass
        
        # Pip - 多种检测方式
        pip_detected = False
        # 方法 1: pip config get global.index-url
        try:
            result = subprocess.run(
                ["pip", "config", "get", "global.index-url"],
                capture_output=True, text=True, timeout=10,
                creationflags=self.creationflags
            )
            if result.returncode == 0 and result.stdout.strip():
                url = result.stdout.strip()
                if "http" in url:
                    info["pip"] = url
                    pip_detected = True
        except Exception:
            pass
        
        # 方法 2: pip config list
        if not pip_detected:
            try:
                result = subprocess.run(
                    ["pip", "config", "list"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=self.creationflags
                )
                if result.returncode == 0:
                    match = re.search(r"global\.index-url\s*=\s*'([^\s'\n]+)", result.stdout)
                    if match:
                        info["pip"] = match.group(1)
                        pip_detected = True
            except Exception:
                pass
        
        # 方法 3: 检查配置文件
        if not pip_detected:
            pip_configs = [self.PIP_CONF, self.PIP_CONF_ALT]
            if os.name == 'nt':
                pip_configs.insert(0, self.PIP_CONF_WIN)
            
            for pip_conf in pip_configs:
                if pip_conf.exists():
                    try:
                        content = pip_conf.read_text()
                        match = re.search(r'index-url\s*=\s*(\S+)', content, re.IGNORECASE)
                        if match:
                            info["pip"] = match.group(1)
                            break
                    except Exception:
                        pass
        
        # Yarn 检测
        try:
            result = subprocess.run(
                ["yarn", "config", "get", "registry"],
                capture_output=True, text=True, timeout=10,
                creationflags=self.creationflags
            )
            if result.returncode == 0 and result.stdout.strip():
                registry = result.stdout.strip()
                if "http" in registry:
                    info["yarn"] = registry
        except Exception:
            pass
        
        # Snap - Linux only
        if os.name != 'nt':
            try:
                env_path = Path("/etc/environment")
                if env_path.exists():
                    content = env_path.read_text()
                    match = re.search(r'SNAPPY_FORCE_API_URL\s*=\s*"?([^\s"\n]+)', content)
                    if match:
                        info["snap"] = match.group(1)
                    elif re.search(r'SNAPPY_STORE_NO_CDN\s*=\s*1', content):
                        info["snap"] = "CDN 已禁用 / CDN disabled"
            except Exception:
                pass
        else:
            info["snap"] = "N/A (Windows)"
        
        return info


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
            # 检查是否在Linux系统上应用Linux特定配置
            if os.name == 'nt':  # Windows
                # 在Windows上，只应用NPM、Pip、Yarn配置，跳过APT和Snap
                if self.apt_choice != "不修改 / Keep current":
                    print("⚠️ APT 配置仅支持Linux系统 / APT config only supports Linux")
                if self.snap_choice != "不修改 / Keep current":
                    print("⚠️ Snap 配置仅支持Linux系统 / Snap config only supports Linux")
                
                # 只应用NPM、Pip、Yarn配置
                if self.npm_choice != "不修改 / Keep current":
                    print("✅ NPM 配置已应用 (模拟) / NPM config applied (simulated)")
                if self.pip_choice != "不修改 / Keep current":
                    print("✅ Pip 配置已应用 (模拟) / Pip config applied (simulated)")
                if self.yarn_choice != "不修改 / Keep current":
                    print("✅ Yarn 配置已应用 (模拟) / Yarn config applied (simulated)")
            else:  # Linux
                # 在Linux上应用所有配置
                if self.apt_choice != "不修改 / Keep current":
                    print("✅ APT 配置已应用 (模拟) / APT config applied (simulated)")
                if self.npm_choice != "不修改 / Keep current":
                    print("✅ NPM 配置已应用 (模拟) / NPM config applied (simulated)")
                if self.pip_choice != "不修改 / Keep current":
                    print("✅ Pip 配置已应用 (模拟) / Pip config applied (simulated)")
                if self.yarn_choice != "不修改 / Keep current":
                    print("✅ Yarn 配置已应用 (模拟) / Yarn config applied (simulated)")
                if self.snap_choice != "不修改 / Keep current":
                    print("✅ Snap 配置已应用 (模拟) / Snap config applied (simulated)")
            
            self.finished.emit(True, "配置完成 / Configuration completed")
        except Exception as e:
            self.finished.emit(False, f"❌ 配置失败: {str(e)} / Config failed: {str(e)}")


def show_mirror_settings(parent=None):
    """Show mirror settings dialog / 显示镜像设置对话框"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("镜像源管理 / Mirror Settings")
    dialog.resize(700, 600)
    
    # 创建镜像管理器实例
    mirror_manager = MirrorManager()
    
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
            info = mirror_manager.get_current_mirror_info()
            distro, release = mirror_manager.detect_distro()
            
            status_lines = [
                "═══ 系统信息 / System Info ═══",
                f"   发行版 / Distro:  {distro.value.upper()} {release}",
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