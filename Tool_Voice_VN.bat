@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Chua cai dat ^(thieu .venv^). Hay chay "cai_dat.bat" truoc.
    echo.
    pause
    exit /b 1
)

echo Dang mo Tool Voice VN ... (lan dau se nap model, vui long doi)
".venv\Scripts\python.exe" tts_gui.py

echo.
echo ============================================================
echo   App da dong. Neu co dong chu mau do / Traceback o tren
echo   -^> chup man hinh nay gui lai de sua loi.
echo ============================================================
pause
