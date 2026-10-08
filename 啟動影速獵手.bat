@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "runtime\pythonw.exe" (
    start "" "runtime\pythonw.exe" "%~dp0cli.py" --open-dashboard
) else (
    start "" pythonw.exe "%~dp0cli.py" --open-dashboard
)
