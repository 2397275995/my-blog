@echo off
title iielxy 博客后台
cd /d "%~dp0admin"

set "PY=C:\Users\23972\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

echo 正在启动后台管理服务…
echo 浏览器会自动打开 http://127.0.0.1:8910/
echo 关闭本窗口即停止服务。
echo.
"%PY%" admin.py
pause
