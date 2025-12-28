@echo off
REM Windows Build Script / Windows 打包脚本
REM This script builds the application into a single .exe file
REM 此脚本将应用打包为单个 .exe 文件

echo =============================================
echo  Clash Env Cleaner - Windows Build Script
echo  Clash 环境清理工具 - Windows 打包脚本
echo =============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    echo [错误] 未找到 Python！请安装 Python 3.10+
    exit /b 1
)

REM Create virtual environment if not exists
if not exist "venv" (
    echo [INFO] Creating virtual environment... / 创建虚拟环境...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment... / 激活虚拟环境...
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies... / 安装依赖...
pip install -r requirements.txt
pip install pyinstaller

REM Build with PyInstaller
echo [INFO] Building with PyInstaller... / 使用 PyInstaller 打包...
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "ClashEnvCleaner" ^
    --add-data "src;src" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.QtCore" ^
    src\main.py

if errorlevel 1 (
    echo [ERROR] Build failed! / 打包失败！
    exit /b 1
)

echo.
echo =============================================
echo [SUCCESS] Build completed! / 打包完成！
echo Output: dist\ClashEnvCleaner.exe
echo 输出文件: dist\ClashEnvCleaner.exe
echo =============================================

REM Deactivate virtual environment
deactivate
