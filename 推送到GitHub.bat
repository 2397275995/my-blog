@echo off
title 推送到 GitHub
cd /d "%~dp0"
set "LOG=%TEMP%\blog-push.log"

echo ================================================
echo   推送博客项目到 GitHub
echo   仓库：https://github.com/2397275995/my-blog
echo ================================================
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
  echo [x] 当前目录不是 git 仓库：%CD%
  pause
  exit /b 1
)

echo === 第一步：同步远端 ===
git pull --rebase origin main > "%LOG%" 2>&1
if errorlevel 1 goto pulllog
echo 已同步。
goto push

:pulllog
type "%LOG%"
echo.

findstr /C:"CONFLICT" /C:"Automatic merge failed" "%LOG%" >nul
if not errorlevel 1 (
  echo [x] 和远端内容冲突，需要按数据结构合并。
  echo     先执行：git rebase --abort
  echo     然后把情况告诉 WorkBuddy，别自己手改 content.json。
  pause
  exit /b 1
)

findstr /C:"Could not connect" /C:"Failed to connect" /C:"timed out" /C:"Could not resolve host" /C:"Connection refused" "%LOG%" >nul
if not errorlevel 1 (
  echo [!] 连不上 GitHub，这是网络问题，不是代码问题。
  echo     1. 等几分钟重试，或者换网络 / 开代理
  echo     2. 有代理可以设：git config --global http.proxy http://127.0.0.1:端口
  echo     3. 网络恢复后重新运行本脚本即可，本地提交不会丢
  pause
  exit /b 1
)

echo [x] 同步失败，原因见上面的输出。
pause
exit /b 1

:push
echo.
echo === 第二步：推送 ===
git push -u origin main > "%LOG%" 2>&1
if errorlevel 1 goto pushlog
type "%LOG%"
echo.
echo [OK] 推送成功。
echo.
echo 接下来 EdgeOne 会自动构建，约两分钟后线上生效。
echo 刷新页面时按 Ctrl+Shift+R 强刷。
echo.
pause
exit /b 0

:pushlog
type "%LOG%"
echo.
findstr /C:"Could not connect" /C:"Failed to connect" /C:"timed out" /C:"Could not resolve host" "%LOG%" >nul
if not errorlevel 1 (
  echo [!] 推送时连不上 GitHub，网络问题。本地提交都还在，稍后重试即可。
  pause
  exit /b 1
)
findstr /C:"rejected" /C:"non-fast-forward" "%LOG%" >nul
if not errorlevel 1 (
  echo [x] 远端又有新的提交了。再运行一次本脚本，它会先拉取再推。
  pause
  exit /b 1
)
echo [x] 推送失败，原因见上面的输出。
pause
exit /b 1
