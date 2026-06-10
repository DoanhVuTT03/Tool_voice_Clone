@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Chua cai dat moi truong. Chay cai_dat.bat truoc.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" admin_tool.py
echo.
echo (Admin tool da dong.)
pause
