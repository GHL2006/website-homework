@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 项目自带 .deps 中的 web.py 和 PyMySQL，免安装即可运行
if exist "..\.deps" set "PYTHONPATH=%~dp0..\.deps;%PYTHONPATH%"

rem 优先使用 Python 3.8（本机已安装），否则使用系统默认 Python
where py >nul 2>nul
if not errorlevel 1 (
    py -3.8 app.py 8080
) else (
    python app.py 8080
)

pause
