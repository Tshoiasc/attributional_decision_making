@echo off
chcp 65001 > nul
title 心理学实验程序启动器

echo ====================================================
echo 心理学实验程序启动器
echo 内在与外在驱动：决策权衡实验
echo ====================================================
echo.

REM 获取当前批处理文件所在目录
cd /d "%~dp0"
echo 当前工作目录: %CD%
echo.

REM 检查Python是否可用
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请确保Python已安装并添加到PATH环境变量中
    echo 尝试使用py命令...
    py --version >nul 2>&1
    if errorlevel 1 (
        echo 错误：py命令也不可用，请检查Python安装
        goto :error_exit
    ) else (
        echo 找到Python (py命令)
        set PYTHON_CMD=py
    )
) else (
    echo 找到Python
    set PYTHON_CMD=python
)
echo.

REM 检查必要文件是否存在
echo 检查程序文件...
if not exist "start_experiment.py" (
    echo 错误：未找到 start_experiment.py 文件
    echo 请确保批处理文件与程序文件在同一目录下
    goto :error_exit
)

if not exist "participant_info_window.py" (
    echo 错误：未找到 participant_info_window.py 文件
    goto :error_exit
)

if not exist "main.py" (
    echo 错误：未找到 main.py 文件
    goto :error_exit
)

if not exist "config.json" (
    echo 错误：未找到 config.json 配置文件
    goto :error_exit
)

echo 所有必要文件检查通过
echo.

REM 启动程序
echo 正在启动被试信息录入窗口...
echo 执行命令: %PYTHON_CMD% start_experiment.py
echo.

%PYTHON_CMD% start_experiment.py

REM 检查程序执行结果
if errorlevel 1 (
    echo.
    echo 程序执行过程中出现错误 (错误代码: %errorlevel%)
    echo 请检查以下可能的问题：
    echo 1. Python依赖包是否完整安装 (pygame, tkinter等)
    echo 2. 程序文件是否完整
    echo 3. 配置文件是否正确
) else (
    echo.
    echo 程序执行完成
)

goto :normal_exit

:error_exit
echo.
echo 程序启动失败，请检查上述错误信息
goto :pause_exit

:normal_exit
echo.
echo 实验程序已结束

:pause_exit
echo.
echo 按任意键退出...
pause > nul
