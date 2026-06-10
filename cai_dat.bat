@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "VPY=%~dp0.venv\Scripts\python.exe"

echo ============================================================
echo   CAI DAT Tool Voice Clone (Doanhbadboiz)
echo   Can INTERNET. Lan dau tai ~vai GB (chi 1 lan). DUNG TAT cua so.
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
    echo Dang cai Python 3.11 (im lang, KHONG can admin)...
    "%TEMP%\py311_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 Shortcuts=0
    set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)
if not exist "%PYEXE%" goto :nopy
echo Python OK: %PYEXE%
echo.

REM --- Thu cua so cai dat dep (neu chay duoc) ---
echo Mo cua so cai dat (neu khong hien, se cai bang dong lenh)...
"%PYEXE%" "%~dp0setup_gui.py" "%PYEXE%" 2>nul

REM --- Da cai DU chua? (thu import torch + omnivoice) ---
call :check
if defined DONE goto :ok

echo.
echo ============================================================
echo   CAI BANG DONG LENH (hien ro tien trinh - vui long doi)
echo ============================================================
echo [1/5] Tao moi truong ao .venv ...
"%PYEXE%" -m venv .venv
echo [2/5] Nang cap pip ...
"%VPY%" -m pip install --upgrade pip
echo [3/5] Cai PyTorch (GPU CUDA 12.8, tu lui CPU) - tai ~2-3GB ...
"%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 "%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0 torchaudio==2.8.0
echo [4/5] Cai OmniVoice + thu vien ...
"%VPY%" -m pip install --retries 10 --timeout 120 -r requirements.txt
echo [5/5] Tai san model OmniVoice (VN + Base) - ~vai GB ...
"%VPY%" download_models.py

call :check
echo.
if not defined DONE (
    echo [LOI] Cai dat CHUA xong. Xem dong loi mau o tren.
    echo       Thuong do rot mang -> cu CHAY LAI file nay (no tai tiep).
    echo.
    pause
    exit /b 1
)
echo === CAI DAT XONG! Dang mo Tool... ===
echo.
pause

:ok
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0tts_gui.py"
exit /b 0

:check
set "DONE="
if exist "%VPY%" ( "%VPY%" -c "import torch, omnivoice" >nul 2>nul && set "DONE=1" )
goto :eof

:nopy
echo.
echo [LOI] Khong tu cai duoc Python 3.11.
echo       Tai tay: https://www.python.org/downloads/release/python-3119/
echo       (tich "Add Python to PATH"), roi chay lai file nay.
echo.
pause
exit /b 1
