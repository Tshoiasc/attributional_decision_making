@echo off
chcp 65001 > nul
echo ====================================================
echo 心理学实验程序启动器
echo 内在与外在驱动：决策权衡实验
echo ====================================================
echo.

echo 正在启动被试信息录入窗口...
python start_experiment.py

echo.
echo 实验程序已结束
pause
