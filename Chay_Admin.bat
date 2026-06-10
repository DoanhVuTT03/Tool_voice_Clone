@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Mo Admin tool bang pythonw (khong hien cmd). Uu tien venv, roi Python he thong.
if exist ".venv\Scripts\pythonw.exe" goto :venv
if exist "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" goto :sys
pyw -3.11 "%~dp0admin_tool.py"
goto :eof

:venv
start "" ".venv\Scripts\pythonw.exe" "%~dp0admin_tool.py"
goto :eof

:sys
start "" "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" "%~dp0admin_tool.py"
goto :eof
