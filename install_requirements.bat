@echo off
chcp 65001 > nul
title Python依赖包安装器

echo ====================================================
echo Python依赖包安装器
echo 心理学实验程序所需依赖
echo ====================================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查Python
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python命令不可用，尝试py命令...
    py --version >nul 2>&1
    if errorlevel 1 (
        echo 错误：未找到Python，请先安装Python
        echo 下载地址：https://www.python.org/downloads/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
        echo 找到Python (py命令)
    )
) else (
    set PYTHON_CMD=python
    echo 找到Python
)

echo Python版本信息：
%PYTHON_CMD% --version
echo.

REM 升级pip
echo 升级pip...
%PYTHON_CMD% -m pip install --upgrade pip
echo.

REM 安装依赖包
echo 安装pygame...
%PYTHON_CMD% -m pip install pygame
echo.

echo 验证tkinter (Python内置)...
%PYTHON_CMD% -c "import tkinter; print('tkinter 可用')"
if errorlevel 1 (
    echo 警告：tkinter不可用，可能需要重新安装Python并勾选tkinter选项
)
echo.

echo 安装其他依赖...
if exist "requirements.txt" (
    echo 发现requirements.txt，安装所有依赖...
    %PYTHON_CMD% -m pip install -r requirements.txt
) else (
    echo 手动安装常用依赖...
    %PYTHON_CMD% -m pip install pygame pillow
)
echo.

echo 依赖包安装完成！
echo 现在可以尝试运行程序了
echo.
pause
