@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   CAI DAT engine WSL (tang toc tao voice) - Tool Voice Clone
echo ============================================================
echo.

REM --- Kiem tra WSL co san khong (dung goto, KHONG dung khoi ngoac) ---
wsl.exe --status >nul 2>nul
if not errorlevel 1 goto :haswsl

echo May CHUA co WSL. Dang thu CAI TU DONG.
echo.
echo === QUAN TRONG: sap hien cua so UAC xin quyen ADMIN ===
echo   - Bam "Yes / Co" de cho phep cai WSL.
echo   - Cai xong PHAI KHOI DONG LAI may.
echo   - Sau khi khoi dong lai, chay LAI file nay de tiep tuc.
echo.
pause
powershell -NoProfile -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-Command','wsl --install'"
echo.
echo Neu UAC bi tu choi hoac khong cai duoc:
echo   Mo PowerShell quyen Admin va go:  wsl --install
echo   Roi khoi dong lai may, mo lai file nay.
echo.
pause
exit /b 1

:haswsl
echo WSL OK. Dang cai moi truong OmniVoice trong WSL quyen root...
echo Tai PyTorch + OmniVoice + TAI SAN MODEL trong WSL - co the vai GB, chi 1 lan.
echo.
for /f "delims=" %%i in ('wsl.exe wslpath "%~dp0wsl\omni_bootstrap.sh"') do set "WSLSH=%%i"
wsl.exe -u root -- bash "%WSLSH%"
if errorlevel 1 goto :failwsl

echo.
echo === XONG! Engine WSL san sang. Mo app va chon engine OmniVoice WSL. ===
echo.
pause
exit /b 0

:failwsl
echo.
echo [LOI] Cai trong WSL chua xong - thuong do rot mang. Cu CHAY LAI file nay.
echo.
pause
exit /b 1
