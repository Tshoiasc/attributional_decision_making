@echo off
echo 启动Windows输入法修复脚本...

echo 1. 启动输入法服务 (ctfmon.exe)
start ctfmon.exe

echo 2. 启动文本服务框架监控器
schtasks /run /tn "\Microsoft\Windows\TextServicesFramework\MsCtfMonitor" 2>nul

echo 3. 等待服务启动完成...
timeout /t 2 >nul

echo 4. 启动心理学实验程序
python main.py

echo 输入法修复脚本执行完成
pause
