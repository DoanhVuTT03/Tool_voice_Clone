@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   CAI DAT OmniVoice trong WSL (Linux) - de tang toc bang
echo   torch.compile. Chi chay 1 lan. Co the mat vai phut + tai ~vai GB.
echo ============================================================
echo.

REM Kiem tra WSL co san khong
wsl.exe --status >nul 2>nul
if errorlevel 1 (
    echo [LOI] May chua co WSL. Cai WSL truoc:
    echo        Mo PowerShell quyen Admin chay:  wsl --install
    echo        Khoi dong lai may, roi chay lai file nay.
    echo.
    pause
    exit /b 1
)

echo Dang chay bootstrap trong WSL (quyen root)...
for /f "delims=" %%i in ('wsl.exe wslpath "%~dp0wsl\omni_bootstrap.sh"') do set "WSLSH=%%i"
wsl.exe -u root -- bash "%WSLSH%"
if errorlevel 1 (
    echo.
    echo [LOI] Cai dat CHUA xong ^(thuong do RACH MANG khi tai goi^).
    echo        -^> Cu CHAY LAI file nay, pip se tai tiep phan con thieu.
    echo.
    pause
    exit /b 1
)
echo.
echo === CAI DAT XONG ^(da thay TOOLVOICE_OMNI_BOOTSTRAP_DONE^) ===
echo Tiep theo chay:  run_wsl_server.bat
echo.
pause
