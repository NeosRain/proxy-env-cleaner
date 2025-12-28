# Changelog / 更新日志

All notable changes to this project will be documented in this file.

本文档记录项目的所有重要变更。

---

## [1.0.0] - 2025-12-28

### 🎉 首次发布 / Initial Release

#### ✨ 新功能 / New Features

**核心功能 / Core Features:**
- ✅ 跨平台支持（Windows 11 + Linux）
- ✅ 开机自动启动并清理代理设置
- ✅ 系统托盘常驻，支持右键菜单操作
- ✅ 完整的双语界面（中文/英文）

**Windows 清理范围:**
- ✅ 系统代理设置（Internet Settings）
- ✅ 环境变量代理（http_proxy、https_proxy、all_proxy、socks_proxy 等）
- ✅ Git 全局代理配置
- ✅ NPM/Yarn 代理配置
- ✅ Pip 代理配置
- ✅ DNS 缓存自动刷新
- ✅ UWP 回环豁免检测
- ✅ Winsock 重置功能（需管理员权限）

**Linux 清理范围:**
- ✅ GNOME 系统代理设置
- ✅ KDE 系统代理设置
- ✅ KDE 应用代理配置（Discover、System Settings 等）
- ✅ Shell 环境变量代理（.bashrc、.zshrc、.profile 等）
- ✅ Git 全局代理配置
- ✅ APT 代理配置文件（支持多个位置）
- ✅ NPM/Yarn 代理配置
- ✅ Pip 代理配置
- ✅ Wget/Curl 代理配置
- ✅ 软件源代理智能检测
- ✅ **软件源自动备份**（最多保留 5 个历史备份）

**GUI 功能:**
- ✅ 实时环境状态检测
- ✅ 可视化清理选项
- ✅ 详细操作日志显示
- ✅ 托盘菜单快捷操作

**托盘菜单:**
- ✅ 显示主窗口
- ✅ 一键清理
- ✅ 清理后退出
- ✅ 退出程序

#### 🔧 技术栈 / Tech Stack
- Python 3.10+
- PyQt6 (GUI 框架)
- pywin32 (Windows 系统操作)
- PyInstaller (程序打包)

#### 📦 构建方式 / Build
- Windows: 单文件 .exe 可执行文件
- Linux: 二进制文件 + .deb 安装包

#### 🌐 自动化 / Automation
- ✅ GitHub Actions 自动构建
- ✅ 自动发布 Release
- ✅ 多平台并行构建

---

## [Unreleased] / 未发布

### 计划功能 / Planned Features
- [ ] macOS 支持
- [ ] Docker 代理配置清理
- [ ] VSCode 插件代理清理
- [ ] 浏览器扩展代理清理
- [ ] 配置导入/导出功能
- [ ] 清理计划任务（定时清理）
- [ ] 更多主题支持

---

## 版本号规范 / Version Format

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

---

## 贡献者 / Contributors

感谢所有为本项目做出贡献的开发者！

Thanks to all contributors who have helped with this project!

---

[1.0.0]: https://github.com/NeosRain/proxy-env-cleaner/releases/tag/v1.0.0
