@echo off
chcp 65001 >nul
title 影速獵手 - 一鍵安裝與註冊精靈
cd /d "%~dp0"

echo ========================================================
echo          🎬 影速獵手 (VideoHunter) 全自動安裝精靈
echo ========================================================
echo.
echo [1/3] 正在註冊 Windows 右鍵選單...
if exist "runtime\python.exe" (
    "runtime\python.exe" setup_right_click.py
) else (
    python setup_right_click.py
)

echo.
echo [2/3] 正在建立桌面捷徑與開機自啟動...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$WshShell = New-Object -comObject WScript.Shell;" ^
  "$Desktop = [System.Environment]::GetFolderPath('Desktop');" ^
  "$Startup = [System.Environment]::GetFolderPath('Startup');" ^
  "$AppDir = '%~dp0'.TrimEnd('\');" ^
  "$Pyw = if (Test-Path \"$AppDir\runtime\pythonw.exe\") { \"$AppDir\runtime\pythonw.exe\" } else { 'pythonw.exe' };" ^
  "$S1 = $WshShell.CreateShortcut(\"$Desktop\影速獵手.lnk\");" ^
  "$S1.TargetPath = $Pyw;" ^
  "$S1.Arguments = \"`\"$AppDir\cli.py`\" --open-dashboard\";" ^
  "$S1.WorkingDirectory = $AppDir;" ^
  "$S1.IconLocation = \"$AppDir\app.ico, 0\";" ^
  "$S1.Save();" ^
  "$S2 = $WshShell.CreateShortcut(\"$Desktop\影速獵手_影片庫.lnk\");" ^
  "$Downloads = [System.Environment]::GetFolderPath('UserProfile') + '\Downloads\影速獵手_影片庫';" ^
  "if (-not (Test-Path $Downloads)) { New-Item -ItemType Directory -Path $Downloads -Force | Out-Null };" ^
  "$S2.TargetPath = $Downloads;" ^
  "$S2.Save();" ^
  "$S3 = $WshShell.CreateShortcut(\"$Startup\VideoHunterService.lnk\");" ^
  "$S3.TargetPath = 'wscript.exe';" ^
  "$S3.Arguments = \"`\"$AppDir\start_service.vbs`\"\";" ^
  "$S3.WorkingDirectory = $AppDir;" ^
  "$S3.Save();"

echo.
echo [3/3] 正在啟動背景下載服務...
start "" wscript.exe "%~dp0start_service.vbs"

echo.
echo ========================================================
echo  🎉 安裝完成！「影速獵手」已成功在此電腦啟用！
echo.
echo  ✅ 桌面與資料夾右鍵選單已註冊（展開即可使用）
echo  ✅ 桌面已建立「影速獵手」與「影速獵手_影片庫」捷徑
echo  ✅ 背景下載服務已啟動，並已設定開機自動在背景待命
echo.
echo  【Chrome / Edge 瀏覽器外掛安裝】：
echo   如需在瀏覽器網頁影片上按右鍵下載，請在 Chrome 開啟
echo   chrome://extensions/ 並載入本資料夾內的【extension】即可！
echo ========================================================
echo.
pause
