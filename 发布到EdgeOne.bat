@echo off
chcp 65001 >nul
title 发布到 EdgeOne Pages
cd /d "%~dp0"

setlocal enabledelayedexpansion
set "SITE=simpletheme-static"
set "CFG=edgeone-project.txt"
set "PY=C:\Users\23972\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

echo ================================================
echo   发布到 EdgeOne Pages
echo ================================================
echo.

rem ---------- 1. 检查产物 ----------
if not exist "%SITE%\index.html" (
  echo [x] 找不到 %SITE%\index.html
  echo     请先在后台「构建发布」里点一次「重新构建站点」。
  echo.
  pause
  exit /b 1
)

rem ---------- 2. 是否先重新构建 ----------
set "REBUILD="
set /p REBUILD=先重新构建站点吗？(y/N，改了内容选 y):
if /i "%REBUILD%"=="y" (
  echo.
  echo === 正在构建，约 3 分钟，请勿关闭窗口 ===
  "%PY%" "admin\build.py" --rebuild
  if errorlevel 1 (
    echo.
    echo [x] 构建失败，已中止发布。
    pause
    exit /b 1
  )
  echo.
)

rem ---------- 3. 项目名 ----------
set "PROJ="
if exist "%CFG%" (
  for /f "usebackq delims=" %%a in ("%CFG%") do set "PROJ=%%a"
)
if "%PROJ%"=="" (
  echo.
  echo 第一次使用，需要填一次 EdgeOne 控制台里的「项目名称」。
  echo （就是你上传文件夹时那个项目的名字，之后会记住）
  echo.
  set /p PROJ=项目名称:
  if "!PROJ!"=="" (
    echo [x] 项目名称不能为空。
    pause
    exit /b 1
  )
  > "%CFG%" echo !PROJ!
  echo 已记住，下次不用再填。
)

rem ---------- 4. 检查 npx ----------
where npx >nul 2>&1
if errorlevel 1 (
  echo.
  echo [x] 找不到 npx，请先安装 Node.js: https://nodejs.org
  pause
  exit /b 1
)

rem ---------- 5. 登录状态 ----------
echo.
echo === 检查登录状态 ===
call npx -y edgeone whoami >nul 2>&1
if errorlevel 1 (
  echo 还没登录，接下来会打开浏览器，用腾讯云账号登录一次即可。
  echo （登录状态会保存，以后不用重复登录）
  echo.
  call npx -y edgeone login
  if errorlevel 1 (
    echo.
    echo [x] 登录失败或被取消。
    pause
    exit /b 1
  )
) else (
  echo 已登录。
)

rem ---------- 6. 部署 ----------
echo.
echo === 开始部署：%SITE%  →  项目 %PROJ% ===
echo.
call npx -y edgeone pages deploy "%SITE%" -n "%PROJ%" -e production
set "CODE=%errorlevel%"

echo.
if not "%CODE%"=="0" (
  echo [x] 部署失败，退出码 %CODE%，看上面的输出。
) else (
  echo [✓] 部署完成，去控制台或直接用域名访问吧。
)
echo.
pause
