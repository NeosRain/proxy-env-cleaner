#!/bin/bash
# Linux Build Script / Linux 打包脚本
# This script builds the application into a .deb package
# 此脚本将应用打包为 .deb 包

set -e

echo "============================================="
echo " Clash Env Cleaner - Linux Build Script"
echo " Clash 环境清理工具 - Linux 打包脚本"
echo "============================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/build"
DEB_DIR="$BUILD_DIR/deb"
DIST_DIR="$PROJECT_DIR/dist"

VERSION="1.0.0"
PACKAGE_NAME="clash-env-cleaner"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.10+"
    echo "[错误] 未找到 Python3！请安装 Python 3.10+"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "[INFO] Creating virtual environment... / 创建虚拟环境..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment... / 激活虚拟环境..."
source "$PROJECT_DIR/venv/bin/activate"

# Install dependencies
echo "[INFO] Installing dependencies... / 安装依赖..."
pip install -r "$PROJECT_DIR/requirements.txt"
pip install pyinstaller

# Build with PyInstaller
echo "[INFO] Building with PyInstaller... / 使用 PyInstaller 打包..."
cd "$PROJECT_DIR"
pyinstaller --noconfirm \
    --onefile \
    --windowed \
    --name "clash-env-cleaner" \
    --add-data "src:src" \
    --hidden-import "PyQt6.QtWidgets" \
    --hidden-import "PyQt6.QtGui" \
    --hidden-import "PyQt6.QtCore" \
    src/main.py

if [ $? -ne 0 ]; then
    echo "[ERROR] PyInstaller build failed! / PyInstaller 打包失败！"
    exit 1
fi

echo "[INFO] Creating .deb package... / 创建 .deb 包..."

# Clean and create build directories
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp "$DIST_DIR/clash-env-cleaner" "$DEB_DIR/usr/bin/"
chmod 755 "$DEB_DIR/usr/bin/clash-env-cleaner"

# Create control file
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Depends: libxcb-cursor0
Maintainer: ClashEnvCleaner <contact@example.com>
Description: Clash Environment Cleaner
 A tool to clean Clash proxy environment settings on startup.
 开机自动清理 Clash 代理环境设置的工具。
EOF

# Create postinst script
cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Create autostart entry
AUTOSTART_DIR="/etc/xdg/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/clash-env-cleaner.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=Clash Env Cleaner
Name[zh_CN]=Clash 环境清理工具
Comment=Clean Clash proxy environment settings
Comment[zh_CN]=清理 Clash 代理环境设置
Exec=/usr/bin/clash-env-cleaner
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
DESKTOP

echo "Clash Env Cleaner installed successfully / Clash 环境清理工具安装成功"
EOF
chmod 755 "$DEB_DIR/DEBIAN/postinst"

# Create prerm script
cat > "$DEB_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Remove autostart entry
rm -f /etc/xdg/autostart/clash-env-cleaner.desktop

echo "Clash Env Cleaner removed / Clash 环境清理工具已卸载"
EOF
chmod 755 "$DEB_DIR/DEBIAN/prerm"

# Create desktop entry
cat > "$DEB_DIR/usr/share/applications/clash-env-cleaner.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Clash Env Cleaner
Name[zh_CN]=Clash 环境清理工具
Comment=Clean Clash proxy environment settings
Comment[zh_CN]=清理 Clash 代理环境设置
Exec=/usr/bin/clash-env-cleaner
Icon=clash-env-cleaner
Terminal=false
Categories=Utility;System;
Keywords=clash;proxy;clean;network;
EOF

# Build deb package
echo "[INFO] Building .deb package... / 打包 .deb..."
dpkg-deb --build "$DEB_DIR" "$DIST_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"

if [ $? -ne 0 ]; then
    echo "[ERROR] .deb build failed! / .deb 打包失败！"
    exit 1
fi

# Deactivate virtual environment
deactivate

echo ""
echo "============================================="
echo "[SUCCESS] Build completed! / 打包完成！"
echo "Binary: dist/clash-env-cleaner"
echo "二进制文件: dist/clash-env-cleaner"
echo ""
echo "DEB Package: dist/${PACKAGE_NAME}_${VERSION}_amd64.deb"
echo "DEB 包: dist/${PACKAGE_NAME}_${VERSION}_amd64.deb"
echo "============================================="
