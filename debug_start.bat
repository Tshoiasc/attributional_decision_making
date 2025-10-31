@echo off
chcp 65001 > nul
title 心理学实验程序调试启动器

echo ====================================================
echo 心理学实验程序调试启动器
echo 内在与外在驱动：决策权衡实验
echo ====================================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"
echo 当前目录: %CD%
echo.

echo 环境检查：
echo.

REM 检查Python
echo 1. 检查Python环境
python --version 2>&1
if errorlevel 1 (
    echo    Python命令不可用，尝试py命令
    py --version 2>&1
    if errorlevel 1 (
        echo    错误：Python未安装或未配置PATH
    ) else (
        set PYTHON_CMD=py
        echo    Python可用 (使用py命令)
    )
) else (
    set PYTHON_CMD=python
    echo    Python可用
)
echo.

REM 检查文件
echo 2. 检查程序文件
for %%f in (start_experiment.py participant_info_window.py main.py config.json) do (
    if exist "%%f" (
        echo    ✓ %%f 存在
    ) else (
        echo    ✗ %%f 缺失
    )
)
echo.

REM 检查依赖
echo 3. 检查Python依赖包
%PYTHON_CMD% -c "import tkinter; print('   ✓ tkinter 可用')" 2>nul || echo    ✗ tkinter 不可用
%PYTHON_CMD% -c "import pygame; print('   ✓ pygame 可用')" 2>nul || echo    ✗ pygame 不可用
%PYTHON_CMD% -c "import json; print('   ✓ json 可用')" 2>nul || echo    ✗ json 不可用
echo.

echo 4. 尝试启动程序
echo    执行: %PYTHON_CMD% start_experiment.py
echo.

%PYTHON_CMD% start_experiment.py

echo.
echo 程序执行完毕，返回代码: %errorlevel%
echo.
echo 如果程序无法启动，请检查上述检查项目
echo 特别注意Python和依赖包的安装情况
echo.
pause
