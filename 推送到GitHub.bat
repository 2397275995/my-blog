@echo off
chcp 65001 >nul
title 推送到 GitHub
cd /d "%~dp0"

echo ================================================
echo   推送博客项目到 GitHub
echo   仓库：https://github.com/2397275995/my-blog
echo ================================================
echo.
echo 第一次运行会弹出 GitHub 登录窗口，用浏览器登录并授权即可，
echo 之后凭据会记住，再推就不用登录了。
echo.
pause

git push -u origin main
if errorlevel 1 goto failed

echo.
echo [✓] 推送成功。
echo.
echo 接下来做两件事：
echo   1. 仓库 Settings - Secrets and variables - Actions
echo      - Secret   EDGEONE_TOKEN    填 EdgeOne 的 API Token
echo      - Variable EDGEONE_PROJECT  填 EdgeOne 的项目名称
echo   2. 打开 /write.html 填仓库名、分支、GitHub Token，就能在线写文章了
echo.
pause
exit /b 0

:failed
echo.
echo [x] 推送失败，常见原因：
echo.
echo   1. 仓库不是空的（建仓库时勾了 README / .gitignore）
echo      处理：先执行  git pull --rebase origin main  再运行本脚本
echo      或者确认仓库里没有要保留的内容后，改为强制推送：
echo            git push -u -f origin main
echo.
echo   2. 登录被取消，或账号没有这个仓库的权限
echo      处理：重新运行本脚本，登录时用有权限的账号
echo.
echo   3. 网络问题（国内访问 GitHub 不稳定）
echo      处理：挂代理后重试，或改用 SSH 方式推送
echo.
pause
exit /b 1
