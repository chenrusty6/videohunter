# 影速獵手 macOS 測試版

這是免裝 Python 的 macOS App，沿用瀏覽器控制台。尚未經 Apple Developer ID 簽署或公證。

1. 在「關於這台 Mac」確認晶片：Apple M 系列選 `macOS-arm64`，Intel 選 `macOS-x86_64`。
2. 解壓縮後，把 **VideoHunter.app** 拖入「應用程式」，再開啟它。
3. 控制台會在預設瀏覽器開啟。貼入自己有權下載的影片網址即可開始。
4. 若 macOS 顯示無法驗證開發者，請確認來源與 SHA-256；信任來源後，可依 Apple 說明在「系統設定 → 隱私權與安全性 → 仍要開啟」允許這個 App。
   https://support.apple.com/102445
5. 瀏覽器分頁關閉後服務仍會執行。請在控制台右上按「結束程式」來停止服務；再開啟 App 可回到控制台。

預設影片位置：`~/Downloads/影速獵手_影片庫`。
設定、紀錄、縮圖及日誌位置：`~/Library/Application Support/VideoHunter/`。
移除 App 不會刪除影片或上述個人資料。

## 功能差異

- 支援貼網址、讀取 Mac 剪貼簿、自選下載資料夾、開啟 Finder 資料夾、下載歷史。
- Chrome / Edge 擴充套件可沿用 Windows 發布頁的獨立 ZIP，需要先啟動 Mac App。
- Mac 通知使用 macOS 文字通知；不包含 Windows 的縮圖與通知按鈕。
- Windows 桌面／資料夾右鍵選單及 Windows 開機啟動註冊不適用於 macOS。
- Safari 擴充套件未提供。瀏覽器登入資訊存取可能要求 macOS 額外授權。

## 已驗證與待驗證

建置流程在各架構的 macOS 主機執行 App 啟動、HTTP 控制台、設定／紀錄讀寫、
本機測試影片下載、MP3 轉換、內附 FFmpeg/FFprobe 與正常結束檢查。
只有建置流程成功的檔案才會出現在測試版下載頁。

仍需 Mac 使用者驗收 Finder 雙擊、首次開啟允許流程、資料夾選擇視窗、通知權限、
Chrome/Edge 連動及實際網站下載。自動化測試不等於已完成這些桌面與逐站驗證。

建置主機為 macOS 15；尚未驗證較舊 macOS。
本測試版屬獨立發布，不取代 Windows v1.0.0。
