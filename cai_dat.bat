@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "LOG=%~dp0install_log.txt"
echo Tool Voice Clone - setup log > "%LOG%"

echo ============================================================
echo   CAI DAT Tool Voice Clone (Doanhbadboiz)
echo   Tu dong: Python 3.11 (neu thieu) + thu vien + tai san model.
echo   Can INTERNET. Lan dau tai ~vai GB (chi 1 lan).
echo ============================================================
echo.

REM ---------- 1) Tim / tu cai Python 3.11 (khong can admin) ----------
REM Luon suy ra DUONG DAN python.exe day du -> an toan ca khi ten user co dau cach.
set "PYEXE="
for /f "delims=" %%e in ('py -3.11 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%e"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

if not defined PYEXE (
    echo [1/5] Khong thay Python 3.11 - dang TAI bo cai chinh thuc tu python.org ...
    curl -L -o "%TEMP%\py311_setup.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if not exist "%TEMP%\py311_setup.exe" powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile $env:TEMP'\py311_setup.exe'"
    echo     Dang cai Python 3.11 (im lang, cho user hien tai, KHONG can admin)...
    "%TEMP%\py311_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 Shortcuts=0
    set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)

if not exist "%PYEXE%" goto :nopy
echo     Python OK: %PYEXE%
"%PYEXE%" --version
echo.

REM ---------- 2) Moi truong ao .venv ----------
echo [2/5] Tao moi truong ao .venv ...
if not exist ".venv\Scripts\python.exe" "%PYEXE%" -m venv .venv
if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Tao .venv that bai. Xem install_log.txt
    echo.
    pause
    exit /b 1
)
set "VPY=%~dp0.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
echo     OK
echo.

REM ---------- 3) PyTorch ----------
echo [3/5] Cai PyTorch (CUDA 12.8, tu lui CPU neu loi) - co the tai ~2-3GB ...
"%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128 >> "%LOG%" 2>&1
if errorlevel 1 (
    echo     Ban GPU loi -> thu ban CPU ...
    "%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0 torchaudio==2.8.0 >> "%LOG%" 2>&1
)
echo     OK
echo.

REM ---------- 4) OmniVoice + thu vien ----------
echo [4/5] Cai OmniVoice + thu vien xu ly ...
"%VPY%" -m pip install --retries 10 --timeout 120 -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [LOI] Cai thu vien that bai. Xem install_log.txt
    echo.
    pause
    exit /b 1
)
echo     OK
echo.

REM ---------- 5) Tai san model (VN + Base) ----------
echo [5/5] Tai san model OmniVoice (VN + Base) - ~vai GB, chi 1 lan ...
"%VPY%" download_models.py
echo.

echo ============================================================
echo   CAI DAT XONG! Mo app bang shortcut "Tool Voice Clone".
echo   Muon engine WSL nhanh hon: chay them  cai_dat_wsl.bat
echo ============================================================
echo.
pause
exit /b 0

:nopy
echo.
echo [LOI] Khong tu cai duoc Python 3.11.
echo       Hay tai tay: https://www.python.org/downloads/release/python-3119/
echo       (nho tich "Add Python to PATH"), roi chay lai file nay.
echo.
pause
exit /b 1
