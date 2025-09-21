@echo off
chcp 65001 >nul
echo ==================================================
echo 心理学实验程序打包工具 (Windows)
echo ==================================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo 正在清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM 清理所有__pycache__目录
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo 正在安装依赖...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo 依赖安装失败
    pause
    exit /b 1
)

python -m pip install pyinstaller
if errorlevel 1 (
    echo PyInstaller安装失败
    pause
    exit /b 1
)

echo.
echo 正在构建可执行文件...
python -m pyinstaller --clean build_exe.spec
if errorlevel 1 (
    echo 构建失败
    pause
    exit /b 1
)

echo.
echo ==================================================
echo 打包完成！
echo 可执行文件位于: dist\心理学实验程序.exe
echo ==================================================

REM 显示文件大小
if exist "dist\心理学实验程序.exe" (
    for %%A in ("dist\心理学实验程序.exe") do echo 文件大小: %%~zA 字节
)

echo.
echo 按任意键退出...
pause >nul
