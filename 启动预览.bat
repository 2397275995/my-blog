@echo off
title SimpleTheme æ≤Ã¨’æ °§ ±æµÿ‘§¿¿
cd /d "%~dp0"

set "PY=C:\Users\23972\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%~dp0serve.py"
pause
