@echo off
chcp 65001 >nul
title QuickSub AI - WebGPU Local Subtitle Generator
echo 正在启动 QuickSub AI WebGPU 本地网页服务...
python "%~dp0serve.py"
pause
