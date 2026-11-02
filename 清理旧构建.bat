@echo off
chcp 65001 >nul
title 清理旧构建副本
cd /d "%~dp0"

set "PY=C:\Users\23972\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%~dp0clean_build.py"
