import os
import re
import urllib.request
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ICON_PATH = str(BASE_DIR / "icon.png")
THUMB_DIR = BASE_DIR / "thumbnails"
THUMB_DIR.mkdir(exist_ok=True)

# Standard PowerShell AUMID that has full access to Windows 10/11 Notification subsystem
SYSTEM_AUMID = "{1AC0E4F8-1420-48E9-AA29-764E7C3575E7}\\WindowsPowerShell\\v1.0\\powershell.exe"

import hashlib
import base64

def get_thumb_path(identifier: str) -> Path:
    h = hashlib.md5(identifier.encode("utf-8", errors="ignore")).hexdigest()
    return THUMB_DIR / f"thumb_{h}.jpg"

def download_thumbnail(thumbnail_url: str, name_hint: str = "thumb") -> str:
    if not thumbnail_url:
        return ""
    out_file = get_thumb_path(thumbnail_url)
    try:
        req = urllib.request.Request(
            thumbnail_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
            if len(data) > 500:
                with open(out_file, "wb") as f:
                    f.write(data)
                return str(out_file)
    except Exception as e:
        print(f"[縮圖下載失敗] {e}")
    return ""

def extract_video_frame(video_path: str) -> str:
    if not video_path or not os.path.exists(video_path):
        return ""
    
    # Try finding ffmpeg
    from .downloader import find_ffmpeg
    ffmpeg_bin = find_ffmpeg()
    ffmpeg_exe = os.path.join(ffmpeg_bin, "ffmpeg.exe") if ffmpeg_bin else "ffmpeg"
    
    out_thumb = get_thumb_path(video_path)
    
    try:
        cmd = [
            ffmpeg_exe, "-y",
            "-ss", "00:00:01",
            "-i", os.path.abspath(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_thumb)
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        if not out_thumb.exists() or out_thumb.stat().st_size == 0:
            cmd2 = [
                ffmpeg_exe, "-y",
                "-i", os.path.abspath(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(out_thumb)
            ]
            subprocess.run(cmd2, capture_output=True, timeout=5)

        if out_thumb.exists() and out_thumb.stat().st_size > 0:
            return str(out_thumb)
    except Exception as e:
        print(f"[FFmpeg 畫面截圖失敗] {e}")
    return ""

def show_native_toast(title: str, msg: str, hero_image: str = "", action_label: str = "", action_launch: str = ""):
    icon_path = str(ICON_PATH).replace("\\", "/")
    hero_xml = ""
    if hero_image and os.path.exists(hero_image):
        hero_clean = str(hero_image).replace("\\", "/")
        hero_xml = f'<image placement="hero" src="{hero_clean}" />'

    action_xml = ""
    if action_label and action_launch:
        launch_clean = str(action_launch).replace("\\", "/")
        action_xml = f'<actions><action activationType="protocol" content="{action_label}" arguments="{launch_clean}" /></actions>'

    # Escape XML characters in title & msg
    clean_title = (
        title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
    clean_msg = (
        msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )

    xml_text = (
        f'<toast duration="short">'
        f'<visual>'
        f'<binding template="ToastGeneric">'
        f'<text>{clean_title}</text>'
        f'<text>{clean_msg}</text>'
        f'{hero_xml}'
        f'<image placement="appLogoOverride" src="{icon_path}" />'
        f'</binding>'
        f'</visual>'
        f'{action_xml}'
        f'</toast>'
    )

    # 徹底防止 PowerShell 命令注入：將完整 XML 轉為 UTF-8 Base64 編碼傳遞，杜絕符號與 Here-String 逃逸
    xml_b64 = base64.b64encode(xml_text.encode("utf-8")).decode("ascii")

    ps_code = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$xmlBytes = [System.Convert]::FromBase64String('{xml_b64}')
$xmlStr = [System.Text.Encoding]::UTF8.GetString($xmlBytes)
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($xmlStr)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{SYSTEM_AUMID}')
$notifier.Show($toast)
"""
    try:
        encoded = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True,
            timeout=5
        )
    except Exception as e:
        print(f"[系統通知錯誤] {e}")

def notify_start(title: str, url: str = "", thumbnail_url: str = ""):
    thumb_path = ""
    if thumbnail_url:
        thumb_path = download_thumbnail(thumbnail_url, title)
    
    clean_title = (title[:50] + "...") if len(title) > 50 else title
    show_native_toast(
        title="🚀 影速獵手 · 開始下載",
        msg=f"{clean_title}\n正在背景以最佳畫質處理中...",
        hero_image=thumb_path
    )

def notify_success(title: str, file_path: str = "", thumbnail_path: str = ""):
    hero = ""
    # 1. Remote thumbnail URL
    if thumbnail_path and thumbnail_path.startswith("http"):
        hero = download_thumbnail(thumbnail_path, title)
    elif thumbnail_path and os.path.exists(thumbnail_path):
        hero = thumbnail_path

    # 2. Local video frame extraction if thumbnail missing
    if (not hero or not os.path.exists(hero)) and file_path and os.path.exists(file_path):
        hero = extract_video_frame(file_path)

    clean_title = (title[:50] + "...") if len(title) > 50 else title
    folder = ""
    if file_path:
        p = Path(file_path)
        folder = str(p.parent if p.exists() else p)

    show_native_toast(
        title="🎉 影速獵手 · 下載完成",
        msg=f"{clean_title}\n檔案已妥善儲存",
        hero_image=hero,
        action_label="📁 打開儲存資料夾",
        action_launch=folder
    )

def notify_info(title: str, msg: str = ""):
    show_native_toast(
        title=f"💡 影速獵手 · {title}",
        msg=msg
    )

def notify_error(title: str, error_msg: str = ""):
    clean_title = (title[:40] + "...") if len(title) > 40 else title
    if "login" in error_msg.lower() or "unsupported url" in error_msg.lower():
        user_msg = "該影片可能需要登入或為私人限定內容。請確保已在瀏覽器登入該平台。"
    elif "not found" in error_msg.lower():
        user_msg = "找不到該影片，可能已被作者刪除或設為私人。"
    else:
        user_msg = (error_msg[:70] + "...") if len(error_msg) > 70 else error_msg

    show_native_toast(
        title="⚠️ 影速獵手 · 下載未完成",
        msg=f"{clean_title}\n{user_msg}"
    )
