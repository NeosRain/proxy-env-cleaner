# 代理环境清理工具 / Proxy Environment Cleaner

一个用于清理系统代理设置的跨平台工具，支持 Windows 和 Linux。

## 功能特性 / Features

- ✅ 自动检测系统代理设置
- ✅ 一键清理所有代理配置
- ✅ 支持系统代理、环境变量、Git配置等
- ✅ 镜像源管理功能（APT、NPM、Pip、Yarn、Snap）
- ✅ 跨平台支持（Windows/Linux）
- ✅ 中英文双语界面

## 系统要求 / System Requirements

### Windows
- Windows 10 / Windows 11
- Python 3.7 或更高版本
- 管理员权限（用于清理系统代理）

### Linux
- Ubuntu 18.04+ / Debian 10+ 或其他主流发行版
- Python 3.7 或更高版本
- sudo 权限（用于修改系统配置）

## 依赖要求 / Dependencies

### Python 内置库
- `os` - 系统操作
- `subprocess` - 子进程管理
- `tkinter` - GUI界面（Windows/Linux原生支持）
- `json` - JSON处理
- `urllib` - 网络请求
- `pathlib` - 路径操作
- `re` - 正则表达式
- `shutil` - 文件操作
- `tarfile` - 压缩文件处理

### 无需额外安装的依赖
此工具仅使用 Python 标准库，无需安装任何第三方包。

## 安装方法 / Installation

### 方法1：直接运行
```bash
# 克隆项目
git clone https://github.com/NeosRain/proxy-env-cleaner.git

# 进入项目目录
cd proxy-env-cleaner

# 运行主程序
python -m src.main
```

### 方法2：下载源码
1. 从 [Releases](https://github.com/NeosRain/proxy-env-cleaner/releases) 下载最新版本
2. 解压后运行 `python -m src.main`

## 使用方法 / Usage

### 启动程序
```bash
python -m src.main
```

### 主要功能
1. **代理清理** - 自动检测并清理各种代理设置
2. **镜像源管理** - 管理各类包管理器的镜像源

### 镜像源管理支持
- **APT** (Linux) - Ubuntu/Debian软件源
- **NPM** - Node.js包管理器
- **Pip** - Python包管理器
- **Yarn** - JavaScript包管理器
- **Snap** (Linux) - Snap软件包

## 支持的镜像源 / Supported Mirrors

- 清华大学开源软件镜像站
- 阿里云开源镜像站
- 中国科学技术大学开源软件镜像
- 华为云镜像站
- 腾讯云镜像站

## 常见问题 / FAQ

### Q: Windows上出现"找不到tkinter"错误？
A: 确保安装了完整的Python，tkinter是Python标准库的一部分。

### Q: Linux上需要什么权限？
A: 清理系统代理和APT源需要sudo权限。

### Q: 如何备份当前配置？
A: 镜像源管理功能会自动备份当前配置，最多保留5个备份。

## 许可证 / License

MIT License

## CI/CD

本项目使用 GitHub Actions 进行持续集成和部署：

- **测试**: 每次推送和拉取请求时运行测试
- **代码质量**: 自动进行代码格式检查和类型检查
- **安全扫描**: 定期扫描代码和依赖的安全漏洞
- **构建和发布**: 当创建标签时自动构建Windows和Linux发行版

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request。

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request。

## 更新日志 / Changelog

### v1.2.6
- 使用tkinter重构GUI，解决Windows兼容性问题
- 无需额外依赖，使用Python内置库

### v1.2.5
- 修复Windows闪退问题
- 优化磨砂玻璃效果

### v1.2.4
- 添加Yarn配置支持
- 完善GUI选项

### v1.2.3
- 增强多种检测方法
- 添加配置验证机制
- 防重复配置功能

### v1.2.2
- 修复Windows上NPM/Pip检测问题
- 添加磨砂玻璃按钮样式

### v1.2.1
- 增大对话框尺寸
- 优化状态显示格式

### v1.2.0
- 添加暗色模式适配
- 实现镜像源在线获取
- 支持Snap源切换

### v1.1.0
- 首次发布镜像源管理功能
- 支持自动检测和智能切换

### v1.0.0
- 初始版本
- 基础代理清理功能