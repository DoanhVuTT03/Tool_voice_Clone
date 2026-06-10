@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   Khoi dong OmniVoice server trong WSL (port 8090, torch.compile)
echo   GIU CUA SO NAY MO trong khi do toc do / dung tool.
echo   Lan dau se warmup bien dich ~1-2 phut, cho den khi thay "SERVER READY".
echo ============================================================
echo.

for /f "delims=" %%i in ('wsl.exe wslpath "%~dp0wsl\omni_run_server.sh"') do set "WSLSH=%%i"
wsl.exe -u root -- bash "%WSLSH%" 8090

echo.
echo (Server da dung. Neu co loi o tren, chup man hinh gui lai.)
pause
