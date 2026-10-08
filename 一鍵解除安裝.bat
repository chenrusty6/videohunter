@echo off
chcp 65001 >nul
title 影速獵手 - 解除安裝精靈
cd /d "%~dp0"

echo ========================================================
echo          🎬 影速獵手 (VideoHunter) 解除安裝精靈
echo ========================================================
echo.
echo 正在清理右鍵選單、桌面捷徑與開機自啟動...

if exist "runtime\python.exe" (
    "runtime\python.exe" setup_right_click.py --uninstall
) else (
    python setup_right_click.py --uninstall
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$Desktop = [System.Environment]::GetFolderPath('Desktop');" ^
  "$Startup = [System.Environment]::GetFolderPath('Startup');" ^
  "Remove-Item \"$Desktop\影速獵手.lnk\" -ErrorAction SilentlyContinue;" ^
  "Remove-Item \"$Desktop\影速獵手_影片庫.lnk\" -ErrorAction SilentlyContinue;" ^
  "Remove-Item \"$Startup\VideoHunterService.lnk\" -ErrorAction SilentlyContinue;"

taskkill /f /im python.exe /fi "WINDOWTITLE eq *VideoHunter*" 2>nul
taskkill /f /im pythonw.exe 2>nul

echo.
echo [OK] 已成功解除安裝並清理所有系統註冊項目！
pause
