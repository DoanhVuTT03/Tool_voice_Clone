@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Da cai (co .venv) -> mo Tool bang pythonw (cua so cmd dong ngay, khong console).
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "%~dp0tts_gui.py"
    exit /b 0
)

REM Chua cai -> chay cai dat (hien tien trinh; cai xong tu mo Tool).
call "%~dp0cai_dat.bat"
exit /b 0
