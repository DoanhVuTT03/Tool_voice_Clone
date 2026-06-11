@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   CAI DAT engine WSL (tang toc tao voice) - Tool Voice Clone
echo ============================================================
echo.

REM --- Kiem tra WSL co san khong (dung goto, KHONG dung khoi ngoac) ---
wsl.exe --status >nul 2>nul
if not errorlevel 1 goto :checkdistro

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

:checkdistro
REM --- WSL co bat, NHUNG phai co IT NHAT 1 ban Linux (distro) chay duoc ---
REM     LUU Y: 'wsl --status' va ca 'wsl -l -q' co the bao OK / exit 0 ke ca khi
REM     CHUA co distro nao (khac nhau theo phien ban WSL). Chac chan nhat la
REM     CHAY THU 1 lenh trong WSL: chua co distro -> wsl tra ve loi (errorlevel<>0).
wsl.exe -u root -- true >nul 2>nul
if errorlevel 1 goto :nodistro
goto :haswsl

:nodistro
echo May da bat WSL nhung CHUA co ban Linux nao - dang cai Ubuntu.
echo.
echo === QUAN TRONG ===
echo   - Cua so cai Ubuntu se hien ra, doi tai xong.
echo   - Khi duoc hoi, hay TAO username va password cho Ubuntu roi nho lai.
echo   - Cai xong, chay LAI file nay de tiep tuc cai OmniVoice.
echo.
pause
wsl.exe --install -d Ubuntu
echo.
echo Neu bao loi quyen, mo PowerShell Admin va go:  wsl --install -d Ubuntu
echo Sau khi tao xong user Ubuntu, CHAY LAI file nay.
echo.
pause
exit /b 1

:haswsl
echo WSL OK. Dang cai moi truong OmniVoice trong WSL quyen root...
echo Tai PyTorch + OmniVoice + TAI SAN MODEL trong WSL - co the vai GB, chi 1 lan.
echo.
set "WSLSH="
for /f "delims=" %%i in ('wsl.exe wslpath "%~dp0wsl\omni_bootstrap.sh"') do set "WSLSH=%%i"
if not defined WSLSH goto :failwsl
wsl.exe -u root -- bash "%WSLSH%"
if errorlevel 1 goto :failwsl
if not "%errorlevel%"=="0" goto :failwsl

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
