@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 优先使用项目自带的 web.py / PyMySQL（在上一级 .deps 目录）
if exist "..\.deps" set "PYTHONPATH=%~dp0..\.deps;%PYTHONPATH%"

where py >nul 2>nul
if not errorlevel 1 (
    py -3.8 app.py 8080
) else (
    python app.py 8080
)

pause
