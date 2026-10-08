import sys
import os
import argparse
import webbrowser
import subprocess
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.config_mgr import load_config, save_config
from core.clipboard import extract_url_from_clipboard
from core.downloader import run_download
from core.notifier import notify_info, notify_error

def choose_folder_dialog(title="影速獵手 · 請選擇資料夾", initial_dir=None):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title, initialdir=initial_dir or str(Path.home()))
        root.destroy()
        return folder
    except Exception as e:
        print(f"[檔案選擇器錯誤] {e}")
        return ""

def open_dashboard():
    cfg = load_config()
    port = cfg.get("port", 58231)
    url = f"http://127.0.0.1:{port}/"
    
    # Try starting server via start_service.vbs if not running
    try:
        import urllib.request
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/config", timeout=1)
    except Exception:
        # Start server silently in background
        vbs_path = BASE_DIR / "start_service.vbs"
        if vbs_path.exists():
            subprocess.Popen(["wscript.exe", str(vbs_path)], shell=False)

    webbrowser.open(url)

def set_default_directory():
    cfg = load_config()
    current_dir = cfg.get("download_dir", "")
    new_dir = choose_folder_dialog(
        title="影速獵手 · 設定預設儲存位置",
        initial_dir=current_dir
    )
    if new_dir and os.path.isdir(new_dir):
        cfg["download_dir"] = new_dir
        save_config(cfg)
        notify_info("預設位置已更新", f"未來影音將預設儲存至：\n{new_dir}")
    else:
        # User canceled
        pass

def main():
    parser = argparse.ArgumentParser(description="影速獵手 - 命令列與系統選單控制器")
    parser.add_argument("--url", type=str, help="影片網址")
    parser.add_argument("--clipboard", action="store_true", help="自剪貼簿讀取網址並下載")
    parser.add_argument("--target-dir", type=str, default="", help="指定下載資料夾路徑")
    parser.add_argument("--pick-dir", action="store_true", help="彈出視窗讓使用者自選下載資料夾")
    parser.add_argument("--set-default-dir", action="store_true", help="設定預設下載位置")
    parser.add_argument("--open-dashboard", action="store_true", help="開啟管理控制台")
    parser.add_argument("--quality", type=str, default="", help="指定畫質：best, 1080p, 720p, mp3")
    
    args = parser.parse_args()

    # 1. Action: Set default directory
    if args.set_default_dir:
        set_default_directory()
        sys.exit(0)

    # 2. Action: Open web dashboard
    if args.open_dashboard:
        open_dashboard()
        sys.exit(0)

    # 3. Action: Download from URL or Clipboard
    url = args.url
    if args.clipboard:
        url = extract_url_from_clipboard()
        if not url:
            notify_error(
                "未偵測到影片網址",
                "請先在瀏覽器複製 YouTube、Facebook、Instagram 等影片網址，再執行下載！"
            )
            sys.exit(0)

    if not url:
        # If no arguments provided, default to opening the dashboard
        open_dashboard()
        sys.exit(0)

    cfg = load_config()
    target_dir = cfg.get("download_dir")

    # If pick-dir was requested:
    if args.pick_dir:
        chosen = choose_folder_dialog(
            title="影速獵手 · 請選擇本次影片下載存放資料夾",
            initial_dir=target_dir
        )
        if not chosen:
            # User canceled
            sys.exit(0)
        target_dir = chosen
    elif args.target_dir and os.path.isdir(args.target_dir):
        target_dir = args.target_dir

    quality = args.quality if args.quality else cfg.get("quality", "best")
    
    run_download(url=url, custom_dir=target_dir, custom_quality=quality)

if __name__ == "__main__":
    main()
