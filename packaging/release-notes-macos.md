原生 macOS App 測試版，無需另外安裝 Python 或 FFmpeg。

- Apple M 系列晶片：下載 **macOS-arm64.zip**。
- Intel Mac：下載 **macOS-x86_64.zip**。
- 解壓縮後，將 **VideoHunter.app** 拖入「應用程式」並開啟；控制台會在瀏覽器顯示。
- 詳細步驟、功能差異及資料位置見附帶的 **Mac-Readme**。

App 在 GitHub 的兩種原生 macOS 主機建置，並通過 App 啟動、控制台、設定與歷史讀寫、本機影片下載、FFmpeg/FFprobe、MP3 轉換及正常停止測試；附帶 smoke-test JSON 與 SHA-256 校驗碼。

本 App 僅有打包工具產生的 ad-hoc 簽章，**尚未完成 Apple Developer ID 簽署與公證**。首次開啟可能需要依 Apple 指示在「系統設定 → 隱私權與安全性」允許來源：https://support.apple.com/102445 。

尚未人工驗收 Finder 雙擊、首次開啟允許流程、資料夾視窗、通知權限、瀏覽器連動及實際各網站下載。Mac 文字通知不含 Windows 縮圖／通知按鈕，Windows 系統右鍵選單不適用。建置主機為 macOS 15；尚未驗證較舊 macOS。

Windows 使用者請繼續使用 **v1.0.0** 的 Windows 免安裝版。
