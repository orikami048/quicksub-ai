@echo off
chcp 65001 >nul
echo 正在还原备份版本的 index.html...
if exist "%~dp0index.html.backup" (
    copy /Y "%~dp0index.html.backup" "%~dp0index.html" >nul
    echo ✅ 已成功还原为重构前的备份版本！
) else (
    echo ❌ 未找到备份文件 index.html.backup
)
pause
