# 🎬 影速獵手 (VideoHunter)

<p align="center">
  <img src="icon.png" width="80" height="80" alt="VideoHunter Logo">
</p>

<p align="center">
  <strong>輕量、高效、全能的 Windows 社群影音下載器與瀏覽器外掛</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Extension-Chrome%20%7C%20Edge%20(MV3)-4285F4?style=flat-square&logo=googlechrome" alt="Chrome Extension">
</p>

---

## ✨ 軟體特色 (Features)

* 🚀 **多平台全面支援**：提供下載支援，實際可用性依網站變更與影片權限而定： **YouTube (最高 4K 原畫 / 提取 MP3 音樂)**、**Threads**、**Facebook (Reels / 影片)**、**Instagram**、**TikTok (抖音)**、**Vimeo (免登入超清)**、**X (Twitter)** 等各大社群影音平台。
* 🖱️ **Windows 系統右鍵深度整合**：在桌面或任何資料夾空白處點擊右鍵，即可展開「影速獵手」子選單，支援剪貼簿一鍵下載、自選下載目錄與控制台切換。
* 🌐 **Chrome / Edge 雙向連動擴充套件**：在網頁任何影片上按右鍵即可觸發本機下載，即時捕捉 DOM 串流直鏈，擺脫傳統下載器頻繁失效問題。
* 🖼️ **原生系統通知與畫面截圖**：下載完成後，右下角彈出 Windows 10/11 原生通知，**直觀呈現影片畫面截圖**，並附有「📁 打開儲存資料夾」按鈕。
* 📦 **純綠色免安裝**：免設定環境、免安裝 Python，解壓縮後點擊 `一鍵安裝與註冊右鍵.bat` 即可在 10 秒內完成所有部署。

---

## 📥 下載與安裝 (Quick Start)

### 方式 A：下載完整免安裝綠色版（推薦）
1. 至本專案的 [Releases 頁面](https://github.com/chenrusty6/videohunter/releases) 下載最新的 **`影速獵手_完整綠色免安裝版.zip`**。
2. 解壓縮至任意資料夾（例如 `D:\影速獵手`）。
3. 雙擊執行目錄內的 **`一鍵安裝與註冊右鍵.bat`**。
4. 完成！系統會自動建立桌面捷徑並註冊 Windows 右鍵選單。

### 方式 B：安裝瀏覽器右鍵擴充套件
1. 打開 Chrome 或 Edge，網址列輸入 `chrome://extensions/`。
2. 開啟右上角 **「開發人員模式」**。
3. 點擊左上角 **「載入未封裝項目」**，選擇專案內的 `extension` 資料夾即可！

---

## 🖥️ 平台支援矩陣

| 平台 | 畫質規格 | 特殊技術特色 |
| :--- | :---: | :--- |
| **YouTube** | 最高 4K HDR / 320k MP3 | 支援即時 JS 挑戰解析，音訊無損轉碼 |
| **Threads** | 1080P 高清原畫 | 獨家 `<script data-sjs>` 深度資料流解析 |
| **Facebook** | 1080P / HD 高清 | 自動清除追蹤參數，支援 Reels / Watch |
| **TikTok / 抖音** | 1080P 無水印原畫 | 支援 `v.douyin.com` 與 `vm.tiktok.com` 短網址重定向 |
| **Vimeo** | 最高 4K 原畫 | 專屬串流轉譯核心，免登入帳號暢快下載 |
| **Instagram** | 串流高品質 MP4 | 瀏覽器 DOM 視訊直鏈即時擷取 |

---

## 🛠️ 目錄結構

```text
videohunter/
├── bin/                    # 內建 FFmpeg / FFprobe 影音合成引擎
├── core/                   # 下載器核心模組 (yt-dlp, notifier, threads extractor)
├── extension/              # Chrome / Edge Manifest V3 擴充套件
├── runtime/                # 內建 Python 3.11 綠色執行環境
├── static/                 # 現代化玻璃擬態 (Glassmorphism) Web 控制台
├── cli.py                  # 命令列與系統選單控制器
├── server.py               # 本機背景守護服務 (127.0.0.1:58231)
├── 一鍵安裝與註冊右鍵.bat     # 自動註冊 Windows 右鍵與桌面捷徑
└── 一鍵解除安裝.bat          # 一鍵乾淨還原所有系統設定
```

---

## 📜 開源許可證 (License)

本專案採用 [MIT License](LICENSE) 授權釋出。歡迎自由分發、客製與貢獻！


## 原始碼執行

Windows / Python 3.11：先安裝 FFmpeg 並加入 PATH，再執行：

```powershell
python -m pip install -r requirements.txt
python server.py
```

開啟 http://127.0.0.1:58231/。個人設定、下載紀錄與縮圖不納入原始碼；首次執行會產生使用者自己的預設設定。
`runtime/` 與 `bin/` 僅附於完整免安裝版 Release，原始碼下載不包含這些目錄。

## v1.0.0 發布檢查

已檢查 Python / JavaScript 語法、壓縮檔完整性與發布檔案 SHA-256。
這次上傳未逐站測試下載、右鍵註冊、通知或新電腦安裝；上方功能與平台表為原作者提供的說明。
桌面程式首次發布為 v1.0.0；附帶的擴充套件 manifest 版本為 1.1.0。
安裝程式會建立捷徑、註冊右鍵選單並加入開機啟動。

## 第三方元件

本專案自有程式碼採 MIT。免安裝版內的 Python、FFmpeg 與其他第三方套件適用各自授權，
詳見 `THIRD_PARTY_NOTICES.md`、FFmpeg 授權副本與 runtime 中的授權檔。
