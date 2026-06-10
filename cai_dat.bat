@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "LOG=%~dp0install_log.txt"
echo Tool Voice VN - install log > "%LOG%"

echo ============================================================
echo   CAI DAT Tool Voice - OmniVoice tieng Viet 1000h (Local)
echo   (chi can chay 1 lan ; moi buoc ghi vao install_log.txt)
echo ============================================================
echo.

REM --- 1) Tim Python (khong dung errorlevel trong ngoac de tranh bug) ---
set "PYCMD="
py -3 --version >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD ( python --version >nul 2>nul && set "PYCMD=python" )
if not defined PYCMD (
    echo [LOI] Khong tim thay Python 3.
    echo        Cai Python 3.10 hoac 3.11 tu https://python.org ^(tich "Add Python to PATH"^),
    echo        sau do chay lai file nay.
    echo.
    pause
    exit /b 1
)
echo Dung Python: %PYCMD%
%PYCMD% --version
echo.

REM --- 2) Tao moi truong ao .venv ---
echo [1/4] Dang tao moi truong ao .venv ...
if not exist ".venv\Scripts\python.exe" (
    %PYCMD% -m venv .venv >> "%LOG%" 2>&1
)
if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Tao .venv that bai. Mo file install_log.txt de xem chi tiet.
    echo        ^(Neu Python la ban Microsoft Store -^> go bo, cai ban tu python.org^)
    echo.
    pause
    exit /b 1
)
set "VPY=%~dp0.venv\Scripts\python.exe"
echo     OK -^> %VPY%
echo.

REM --- 3) Nang cap pip ---
echo [2/4] Dang nang cap pip ...
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [LOI] Nang cap pip that bai. Xem install_log.txt
    echo.
    pause
    exit /b 1
)
echo     OK
echo.

REM --- 4) Cai PyTorch (CUDA 12.8 cho GPU NVIDIA) ---
echo [3/4] Dang cai PyTorch GPU ^(CUDA 12.8^) - co the tai ~2-3GB, doi mot chut ...
"%VPY%" -m pip install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128 >> "%LOG%" 2>&1
if errorlevel 1 (
    echo     [Canh bao] Ban GPU that bai -^> thu cai ban CPU ^(chay cham hon^)...
    "%VPY%" -m pip install torch==2.8.0 torchaudio==2.8.0 >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo [LOI] Cai PyTorch that bai ca GPU lan CPU. Xem install_log.txt
        echo.
        pause
        exit /b 1
    )
)
echo     OK
echo.

REM --- 5) Cai OmniVoice + thu vien audio ---
echo [4/4] Dang cai OmniVoice + thu vien xu ly audio ...
"%VPY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [LOI] Cai OmniVoice that bai. Xem install_log.txt
    echo.
    pause
    exit /b 1
)
echo     OK
echo.

echo ============================================================
echo   XONG! Bay gio chay file:  Tool_Voice_VN.bat
echo   (Lan dau bam Start se TAI MODEL ve ~vai GB - chi 1 lan.)
echo ============================================================
echo.
pause
