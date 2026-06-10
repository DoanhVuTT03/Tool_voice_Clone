@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   CAI DAT Tool Voice Clone (Doanhbadboiz)
echo   Chuan bi Python 3.11, sau do mo CUA SO CAI DAT (tien trinh).
echo ============================================================
echo.

REM --- Tim / tu cai Python 3.11 (khong can admin) ---
set "PYEXE="
for /f "delims=" %%e in ('py -3.11 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%e"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

if not defined PYEXE (
    echo Khong thay Python 3.11 - dang TAI bo cai chinh thuc tu python.org ...
    curl -L -o "%TEMP%\py311_setup.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if not exist "%TEMP%\py311_setup.exe" powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile $env:TEMP'\py311_setup.exe'"
    echo Dang cai Python 3.11 (im lang, cho user hien tai, KHONG can admin)...
    "%TEMP%\py311_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 Shortcuts=0
    set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

if not exist "%PYEXE%" goto :nopy

echo Python OK: %PYEXE%
echo Dang mo cua so cai dat...
"%PYEXE%" "%~dp0setup_gui.py" "%PYEXE%"
exit /b 0

:nopy
echo.
echo [LOI] Khong tu cai duoc Python 3.11.
echo       Tai tay: https://www.python.org/downloads/release/python-3119/
echo       (tich "Add Python to PATH"), roi chay lai file nay.
echo.
pause
exit /b 1
