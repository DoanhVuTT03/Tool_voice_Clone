@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   CAI DAT Tool Voice Clone (Doanhbadboiz)
echo   Can INTERNET. Lan dau tai ~vai GB (chi 1 lan).
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

REM --- Thu mo CUA SO cai dat (co thanh tien trinh) ---
echo Dang mo cua so cai dat... (neu khong hien, se tu cai bang dong lenh ben duoi)
"%PYEXE%" "%~dp0setup_gui.py" "%PYEXE%"

REM --- Neu GUI khong tao duoc .venv -> CAI BANG DONG LENH (hien ro + dung man hinh) ---
if exist "%~dp0.venv\Scripts\python.exe" goto :done

echo.
echo ============================================================
echo   Cua so cai dat khong chay duoc -> CAI BANG DONG LENH
echo ============================================================
set "VPY=%~dp0.venv\Scripts\python.exe"
echo [1/4] Tao moi truong ao .venv ...
"%PYEXE%" -m venv .venv
echo [2/4] Nang cap pip ...
"%VPY%" -m pip install --upgrade pip
echo [3/4] Cai PyTorch (GPU CUDA 12.8, tu lui CPU) - tai ~2-3GB ...
"%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 "%VPY%" -m pip install --retries 10 --timeout 120 torch==2.8.0 torchaudio==2.8.0
echo [4/4] Cai OmniVoice + thu vien ...
"%VPY%" -m pip install --retries 10 --timeout 120 -r requirements.txt
echo [+] Tai san model (VN + Base) - ~vai GB ...
"%VPY%" download_models.py
echo.
if exist "%~dp0.venv\Scripts\python.exe" (
    echo === CAI DAT XONG! Mo lai shortcut "Tool Voice Clone" de dung. ===
) else (
    echo [LOI] Cai dat that bai. Xem dong loi o tren. Co the do rot mang -> chay lai file nay.
)
echo.
pause

:done
exit /b 0

:nopy
echo.
echo [LOI] Khong tu cai duoc Python 3.11.
echo       Tai tay: https://www.python.org/downloads/release/python-3119/
echo       (tich "Add Python to PATH"), roi chay lai file nay.
echo.
pause
exit /b 1
