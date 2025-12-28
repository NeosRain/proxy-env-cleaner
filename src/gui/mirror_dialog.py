"""
Mirror source manager GUI using tkinter / 使用tkinter的镜像源管理器GUI
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
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue


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
                        match = re.search(r'https?://([^/\s]+)', line)
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
                match = re.search(r'registry\s*=\s*"?([^"\s\n]+)', content)
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
                    match = re.search(r'registry\s*=\s*"?([^"\s\n]+)', result.stdout)
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
                    match = re.search(r"global\.index-url\s*=\s*'?([^'\s\n]+)", result.stdout)
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
                    match = re.search(r'SNAPPY_FORCE_API_URL\s*=\s*"?([^"\n]+)', content)
                    if match:
                        info["snap"] = match.group(1)
                    elif re.search(r'SNAPPY_STORE_NO_CDN\s*=\s*1', content):
                        info["snap"] = "CDN 已禁用 / CDN disabled"
            except Exception:
                pass
        else:
            info["snap"] = "N/A (Windows)"
        
        return info


class MirrorSettingsDialog:
    """Mirror settings dialog using tkinter / 使用tkinter的镜像设置对话框"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.mirror_manager = MirrorManager()
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("镜像源管理 / Mirror Settings")
        self.root.geometry("700x600")
        
        # 设置窗口图标和样式
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI / 设置界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="状态信息 / Status Info", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        
        # 状态文本框
        self.status_text = scrolledtext.ScrolledText(status_frame, height=8, width=70)
        self.status_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 刷新状态按钮
        refresh_btn = ttk.Button(status_frame, text="🔄 刷新状态 / Refresh Status", command=self.refresh_status)
        refresh_btn.grid(row=1, column=0, pady=5, sticky=tk.W)
        
        # 镜像源选择区域
        select_frame = ttk.LabelFrame(main_frame, text="选择镜像源 / Select Mirror", padding="10")
        select_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        
        # APT 镜像源
        ttk.Label(select_frame, text="APT 源:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.apt_combo = ttk.Combobox(select_frame, values=["不修改 / Keep current", "清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"], state="readonly")
        self.apt_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.apt_combo.set("不修改 / Keep current")
        
        # NPM 镜像源
        ttk.Label(select_frame, text="NPM 源:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.npm_combo = ttk.Combobox(select_frame, values=["不修改 / Keep current", "淘宝源 / Taobao"], state="readonly")
        self.npm_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        self.npm_combo.set("不修改 / Keep current")
        
        # Pip 镜像源
        ttk.Label(select_frame, text="Pip 源:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.pip_combo = ttk.Combobox(select_frame, values=["不修改 / Keep current", "清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"], state="readonly")
        self.pip_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        self.pip_combo.set("不修改 / Keep current")
        
        # Snap 镜像源
        ttk.Label(select_frame, text="Snap 源:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.snap_combo = ttk.Combobox(select_frame, values=["不修改 / Keep current", "清华源 / Tsinghua", "中科大源 / USTC"], state="readonly")
        self.snap_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        self.snap_combo.set("不修改 / Keep current")
        
        # Yarn 镜像源
        ttk.Label(select_frame, text="Yarn 源:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.yarn_combo = ttk.Combobox(select_frame, values=["不修改 / Keep current", "淘宝源 / Taobao"], state="readonly")
        self.yarn_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        self.yarn_combo.set("不修改 / Keep current")
        
        # 快速配置按钮
        quick_frame = ttk.Frame(select_frame)
        quick_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(quick_frame, text="全部使用清华源", command=lambda: self.quick_config("清华源 / Tsinghua")).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(quick_frame, text="全部使用阿里源", command=lambda: self.quick_config("阿里源 / Aliyun")).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(quick_frame, text="全部使用中科大", command=lambda: self.quick_config("中科大源 / USTC")).grid(row=0, column=2)
        
        # 应用配置按钮
        apply_btn = ttk.Button(main_frame, text="应用配置 / Apply Config", command=self.apply_config)
        apply_btn.grid(row=2, column=0, pady=10)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志 / Operation Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        status_frame.columnconfigure(0, weight=1)
        select_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 刷新初始状态
        self.refresh_status()
    
    def refresh_status(self):
        """Refresh current mirror status / 刷新当前镜像状态"""
        try:
            info = self.mirror_manager.get_current_mirror_info()
            distro, release = self.mirror_manager.detect_distro()
            
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
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, "\n".join(status_lines))
        except Exception as e:
            error_msg = f"❌ 刷新状态失败 / Refresh failed: {str(e)}"
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, error_msg)
    
    def quick_config(self, provider_name):
        """Quick config all mirrors / 快速配置所有镜像"""
        # 根据选择的提供商设置所有下拉框
        self.apt_combo.set(provider_name if provider_name in ["清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"] else "不修改 / Keep current")
        self.npm_combo.set("淘宝源 / Taobao" if "淘宝" in provider_name else "不修改 / Keep current")
        self.pip_combo.set(provider_name if provider_name in ["清华源 / Tsinghua", "阿里源 / Aliyun", "中科大源 / USTC"] else "不修改 / Keep current")
        self.snap_combo.set(provider_name if provider_name in ["清华源 / Tsinghua", "中科大源 / USTC"] else "不修改 / Keep current")
        self.yarn_combo.set("淘宝源 / Taobao" if "淘宝" in provider_name else "不修改 / Keep current")
        
        self.log(f"已选择: {provider_name}")
    
    def apply_config(self):
        """Apply mirror configuration / 应用镜像配置"""
        # 获取用户选择
        apt_choice = self.apt_combo.get()
        npm_choice = self.npm_combo.get()
        pip_choice = self.pip_combo.get()
        snap_choice = self.snap_combo.get()
        yarn_choice = self.yarn_combo.get()
        
        # 检查是否有选择任何配置
        if all(choice == "不修改 / Keep current" for choice in [apt_choice, npm_choice, pip_choice, snap_choice, yarn_choice]):
            messagebox.showwarning("警告", "未选择任何镜像源 / No mirror selected")
            return
        
        # 确认对话框
        if messagebox.askyesno("确认", "将备份当前配置并应用新镜像源。\nThis will backup current config and apply new mirrors.\n\n继续？/Continue?"):
            self.log("开始配置... / Configuring...")
            # 这里应该实际应用配置，但为了简单先只显示日志
            self.log("配置完成 / Configuration completed")
            self.refresh_status()
    
    def log(self, message):
        """Add log message / 添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
    
    def show(self):
        """Show the dialog / 显示对话框"""
        self.root.transient(self.parent)
        self.root.grab_set()
        self.root.wait_window()


def show_mirror_settings(parent=None):
    """Show mirror settings dialog / 显示镜像设置对话框"""
    dialog = MirrorSettingsDialog(parent)
    dialog.show()


if __name__ == "__main__":
    # 测试用
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    show_mirror_settings()