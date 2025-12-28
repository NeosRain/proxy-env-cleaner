# Proxy Environment Cleaner / 代理环境清理工具

<div align="center">

![License](https://img.shields.io/github/license/NeosRain/proxy-env-cleaner)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Release](https://img.shields.io/github/v/release/NeosRain/proxy-env-cleaner)

**开机自动清理所有代理环境设置的跨平台工具**

**Cross-platform tool to automatically clean all proxy environment settings on startup**

[English](#english) | [中文](#中文)

[![GitHub stars](https://img.shields.io/github/stars/NeosRain/proxy-env-cleaner?style=social)](https://github.com/NeosRain/proxy-env-cleaner/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/NeosRain/proxy-env-cleaner?style=social)](https://github.com/NeosRain/proxy-env-cleaner/network/members)

</div>

---

## 中文

### 📋 项目简介

Proxy Environment Cleaner 是一款开源的代理环境清理工具，专为解决代理软件（如 Clash、V2Ray 等）异常退出后遗留的系统代理设置问题而设计。

**核心特性：**
- ✅ **全面清理**：清理系统代理、环境变量、Git、NPM、Pip、APT 等所有代理设置
- ✅ **开机自启**：系统启动时自动清理，无需手动干预
- ✅ **托盘常驻**：最小化到系统托盘，随时一键清理
- ✅ **智能检测**：自动识别并清理各类代理配置
- ✅ **安全备份**：Linux 软件源自动备份（最多保留 5 个）
- ✅ **双语界面**：完整的中文/英文双语支持
- ✅ **跨平台**：支持 Windows 11 和主流 Linux 发行版

---

### 🎯 清理范围

#### Windows 平台
| 类型 | 清理内容 |
|------|---------|
| **系统设置** | Internet Settings 系统代理、代理服务器地址 |
| **环境变量** | http_proxy、https_proxy、all_proxy、no_proxy 等 |
| **开发工具** | Git、NPM、Yarn、Pip 代理配置 |
| **网络优化** | DNS 缓存刷新、Winsock 重置（可选） |
| **UWP 应用** | UWP 回环豁免检测 |

#### Linux 平台
| 类型 | 清理内容 |
|------|---------|
| **桌面环境** | GNOME、KDE 系统代理设置 |
| **KDE 应用** | Discover、System Settings 等 KDE 应用代理 |
| **环境变量** | Shell 配置文件（.bashrc、.zshrc 等）中的代理变量 |
| **开发工具** | Git、NPM、Yarn、Pip 代理配置 |
| **下载工具** | Wget、Curl 代理设置 |
| **包管理器** | APT 代理配置文件（自动检测并清理） |
| **软件源** | sources.list 代理地址智能识别 |

---

### 🚀 快速开始

#### Windows 安装

1. 从 [Releases](https://github.com/NeosRain/proxy-env-cleaner/releases) 下载 `ProxyEnvCleaner.exe`
2. 双击运行即可
3. 程序会自动设置开机自启并最小化到托盘

#### Linux 安装

**Ubuntu/Debian (.deb 包):**
```bash
# 下载 .deb 文件
wget https://github.com/NeosRain/proxy-env-cleaner/releases/latest/download/proxy-env-cleaner_1.0.0_amd64.deb

# 安装
sudo dpkg -i proxy-env-cleaner_*.deb

# 运行
proxy-env-cleaner
```

**其他发行版（二进制文件）:**
```bash
# 下载二进制文件
wget https://github.com/NeosRain/proxy-env-cleaner/releases/latest/download/proxy-env-cleaner

# 赋予执行权限
chmod +x proxy-env-cleaner

# 运行
./proxy-env-cleaner
```

---

### 💡 使用方法

#### 托盘菜单操作

右键点击系统托盘图标：

| 菜单项 | 功能 |
|--------|------|
| **显示主窗口** | 打开主界面，查看检测结果和操作日志 |
| **一键清理** | 立即执行清理操作 |
| **清理后退出** | 清理完成后自动退出程序 |
| **退出** | 直接退出程序 |

#### 主窗口功能

- **环境状态检测**：实时显示当前系统的代理配置状态
- **清理选项**：可自定义选择要清理的项目
- **操作日志**：详细记录每次清理的结果

---

### 🔧 开发指南

#### 环境要求

- Python 3.10+
- PyQt6 6.5.0+
- Windows: pywin32
- Linux: 标准系统工具（gsettings、kwriteconfig 等）

#### 从源码运行

```bash
# 克隆仓库
git clone https://github.com/NeosRain/proxy-env-cleaner.git
cd proxy-env-cleaner

# 安装依赖
pip install -r requirements.txt

# 运行
python src/main.py
```

#### 手动构建

**Windows:**
```bash
# 使用提供的脚本
scripts\build_windows.bat

# 或手动构建
pip install pyinstaller
pyinstaller --onefile --windowed --name ProxyEnvCleaner src/main.py
```

**Linux:**
```bash
# 使用提供的脚本
bash scripts/build_linux.sh

# 或手动构建
pip install pyinstaller
pyinstaller --onefile --windowed --name proxy-env-cleaner src/main.py
```

---

### 📁 项目结构

```
proxy-env-cleaner/
├── src/
│   ├── main.py              # 程序入口
│   ├── core/                # 核心清理逻辑
│   │   ├── cleaner_base.py
│   │   ├── cleaner_windows.py
│   │   ├── cleaner_linux.py
│   │   └── detector.py
│   ├── gui/                 # 图形界面
│   │   ├── main_window.py
│   │   └── tray_icon.py
│   ├── autostart/           # 开机自启
│   │   ├── autostart_windows.py
│   │   └── autostart_linux.py
│   └── utils/               # 工具模块
│       ├── config.py
│       ├── logger.py
│       └── platform_utils.py
├── .github/workflows/       # GitHub Actions
│   └── release.yml
└── scripts/                 # 构建脚本
    ├── build_windows.bat
    └── build_linux.sh
```

---

### 🛡️ 安全说明

- 所有操作均在用户空间执行，不会修改系统核心文件
- Linux 软件源在清理前会自动备份到 `~/.config/ProxyEnvCleaner/backups/sources/`
- 日志文件存储位置：
  - Windows: `%APPDATA%\ProxyEnvCleaner\logs\`
  - Linux: `~/.local/share/ProxyEnvCleaner/logs/`

---

### 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

### 📜 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

### ⭐ Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐

---

## English

### 📋 Introduction

Proxy Environment Cleaner is an open-source tool designed to automatically clean leftover proxy settings from proxy software (like Clash, V2Ray, etc.) after abnormal exits.

**Key Features:**
- ✅ **Comprehensive Cleaning**: Removes all proxy settings from system, environment variables, Git, NPM, Pip, APT, etc.
- ✅ **Auto-start on Boot**: Automatically cleans on system startup
- ✅ **System Tray**: Minimizes to tray for quick access
- ✅ **Smart Detection**: Automatically identifies and cleans various proxy configurations
- ✅ **Safe Backup**: Automatic backup of Linux sources (keeps up to 5)
- ✅ **Bilingual UI**: Full Chinese/English support
- ✅ **Cross-platform**: Supports Windows 11 and major Linux distributions

---

### 🎯 Cleaning Scope

#### Windows Platform
- **System Proxy**: Internet Settings, proxy server addresses
- **Environment Variables**: http_proxy, https_proxy, all_proxy, no_proxy, etc.
- **Development Tools**: Git, NPM, Yarn, Pip proxy configurations
- **Network**: DNS cache flush, Winsock reset (optional)
- **UWP Apps**: UWP loopback exemption detection

#### Linux Platform
- **Desktop Environment**: GNOME, KDE system proxy settings
- **KDE Applications**: Discover, System Settings, etc.
- **Environment Variables**: Proxy settings in shell configs (.bashrc, .zshrc, etc.)
- **Development Tools**: Git, NPM, Yarn, Pip proxy configurations
- **Download Tools**: Wget, Curl proxy settings
- **Package Manager**: APT proxy configuration files
- **Software Sources**: Smart detection of proxy addresses in sources.list

---

### 🚀 Quick Start

#### Windows

1. Download `ProxyEnvCleaner.exe` from [Releases](https://github.com/NeosRain/proxy-env-cleaner/releases)
2. Double-click to run
3. The program will auto-configure startup and minimize to tray

#### Linux

**Ubuntu/Debian (.deb package):**
```bash
wget https://github.com/NeosRain/proxy-env-cleaner/releases/latest/download/proxy-env-cleaner_1.0.0_amd64.deb
sudo dpkg -i proxy-env-cleaner_*.deb
proxy-env-cleaner
```

**Other Distributions (binary):**
```bash
wget https://github.com/NeosRain/proxy-env-cleaner/releases/latest/download/proxy-env-cleaner
chmod +x proxy-env-cleaner
./proxy-env-cleaner
```

---

### 💡 Usage

#### Tray Menu

Right-click the system tray icon:
- **Show Window**: Open main interface
- **Quick Clean**: Execute cleaning immediately
- **Clean & Exit**: Clean and quit
- **Exit**: Quit directly

#### Main Window

- **Environment Status**: Real-time proxy configuration status
- **Clean Options**: Customize items to clean
- **Operation Log**: Detailed cleaning results

---

### 🔧 Development

#### Requirements

- Python 3.10+
- PyQt6 6.5.0+
- Windows: pywin32
- Linux: Standard system tools (gsettings, kwriteconfig, etc.)

#### Run from Source

```bash
git clone https://github.com/NeosRain/proxy-env-cleaner.git
cd proxy-env-cleaner
pip install -r requirements.txt
python src/main.py
```

---

### 📜 License

This project is licensed under the [MIT License](LICENSE).

---

### 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<div align="center">

**Made with ❤️ by Proxy Env Cleaner Team**

</div>
