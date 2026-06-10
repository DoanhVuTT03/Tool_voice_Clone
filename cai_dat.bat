@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "VPY=%~dp0.venv\Scripts\python.exe"

echo ============================================================
echo   CAI DAT Tool Voice Clone - Doanhbadboiz
echo   Can INTERNET. Lan dau tai vai GB chi 1 lan. DUNG TAT cua so.
echo ============================================================
echo.

REM --- Tim Python 3.11 (dung goto, KHONG dung khoi ngoac de tranh loi) ---
set "PYCMD="
py -3.11 -V >nul 2>nul && set "PYCMD=py -3.11"
if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYCMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if defined PYCMD goto :havepy

echo Khong thay Python 3.11 - dang TAI bo cai chinh thuc tu python.org ...
curl -L -o "%TEMP%\py311_setup.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
echo Dang cai Python 3.11 im lang, khong can admin ...
"%TEMP%\py311_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0 Shortcuts=0
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYCMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

:havepy
if not defined PYCMD goto :nopy
echo Python OK.
echo.

echo Mo cua so cai dat - neu khong hien se cai bang dong lenh ...
%PYCMD% "%~dp0setup_gui.py"

call :check
if defined DONE goto :ok

echo.
echo ============================================================
echo   CAI BANG DONG LENH - vui long doi, tai vai GB
echo ============================================================
echo [1/5] Tao moi truong ao .venv ...
%PYCMD% -m venv .venv
echo [2/5] Nang cap pip ...
"%VPY%" -m pip install --upgrade pip
echo [3/5] Cai PyTorch GPU CUDA 12.8, tu lui CPU - tai ~2-3GB ...
"%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 "%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0 torchaudio==2.8.0
echo [4/5] Cai OmniVoice + thu vien ...
"%VPY%" -m pip install --retries 10 --timeout 120 -r requirements.txt
echo [5/5] Tai san model OmniVoice VN + Base - ~vai GB ...
"%VPY%" download_models.py

call :check
echo.
if defined DONE goto :installed
echo [LOI] Cai dat CHUA xong - xem dong loi mau o tren.
echo       Thuong do rot mang -^> cu CHAY LAI file nay, no tai tiep.
echo.
pause
exit /b 1

:installed
echo === CAI DAT XONG! Dang mo Tool... ===
echo.
pause

:ok
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0tts_gui.py"
exit /b 0

:check
set "DONE="
if not exist "%VPY%" goto :eof
"%VPY%" -c "import torch, omnivoice" >nul 2>nul && set "DONE=1"
goto :eof

:nopy
echo.
echo [LOI] Khong tu cai duoc Python 3.11.
echo       Tai tay: https://www.python.org/downloads/release/python-3119/
echo       Tich Add Python to PATH roi chay lai file nay.
echo.
pause
exit /b 1
