@echo off
chcp 65001 >nul
title SimpleTheme 静态站 · 本地预览
cd /d "%~dp0"

set "PY=C:\Users\23972\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%~dp0serve.py"
pause
