import os
import re
import time
import glob
import shutil
import threading
import urllib.request
from pathlib import Path
import yt_dlp

from .config_mgr import load_config, add_history_entry
from .notifier import notify_start, notify_success, notify_info, notify_error

active_tasks = {}
active_lock = threading.Lock()

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}

def find_ffmpeg() -> str:
    local_bin = Path(__file__).resolve().parent.parent / "bin"
    if (local_bin / "ffmpeg.exe").exists():
        bin_str = str(local_bin)
        os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")
        return bin_str

    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return os.path.dirname(which_ffmpeg)
    pattern = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\*ffmpeg*\**\ffmpeg.exe")
    matches = glob.glob(pattern, recursive=True)
    if matches:
        bin_dir = os.path.dirname(matches[0])
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        return bin_dir
    return ""

def clean_and_resolve_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        if "." in url and not url.startswith("http"):
            url = "https://" + url

    # Normalize Threads domain
    if "threads.com" in url:
        url = url.replace("threads.com", "threads.net")

    # Convert Vimeo URLs to embed player URLs to bypass login walls
    if "vimeo.com" in url and "player.vimeo.com" not in url:
        v_match = re.search(r'vimeo\.com/(?:[^/]+/)*?(\d+)', url)
        if v_match:
            url = f"https://player.vimeo.com/video/{v_match.group(1)}"

    # Follow redirects for known social share links
    is_social_share = any(k in url for k in [
        "fb.watch", "facebook.com/share", "vm.tiktok.com", "vt.tiktok.com",
        "v.douyin.com", "t.co", "youtu.be"
    ])
    
    if is_social_share:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=6) as resp:
                resolved = resp.geturl()
                if resolved:
                    url = resolved
        except Exception:
            pass

    # Clean Facebook tracking parameters
    if "facebook.com" in url or "fb.com" in url:
        url = re.sub(r"([?&])(?:mibextid|source|bucket_count|rdid|share_url|sfnsn|extid)=[^&]*", "", url)
        url = url.rstrip("?&")
        url = url.replace("m.facebook.com", "www.facebook.com")

    # Clean Instagram tracking query params
    if "instagram.com" in url or "threads.net" in url:
        url = re.sub(r"([?&])(?:igsh|utm_[^&]+|xmt)=[^&]*", "", url)
        url = url.rstrip("?&")

    return url

def download_threads_fallback(url: str, target_dir: str) -> dict:
    clean_url = clean_and_resolve_url(url)
    req = urllib.request.Request(clean_url, headers=BROWSER_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {"success": False, "error": f"無法存取該貼文: {e}"}

    clean = html.replace("\\u0026", "&").replace("\\/", "/")
    
    t_m = re.search(r"<title>([^<]+)</title>", html)
    title = t_m.group(1).replace(" | Threads", "").strip() if t_m else "Threads 貼文"
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:45]

    all_links = re.findall(r'https://[^\s"\'<>\\]+', clean)
    
    # 1. Check for real video
    vids = [
        u.replace("&amp;", "&") for u in all_links
        if ("cdninstagram.com" in u or "fbcdn.net" in u)
        and (".mp4" in u or "t50." in u)
        and "rsrc.php" not in u and "static" not in u
    ]
    for vid_url in vids:
        try:
            out_path = os.path.join(target_dir, f"{safe_title}.mp4")
            v_req = urllib.request.Request(vid_url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.threads.net/"})
            with urllib.request.urlopen(v_req, timeout=15) as r, open(out_path, "wb") as f:
                f.write(r.read())
            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                return {"success": True, "title": title, "path": out_path, "type": "video"}
        except Exception:
            continue

    # 2. Check for photos (exclude avatars t51.2885-19 and static assets)
    imgs = [
        u.replace("&amp;", "&") for u in all_links
        if ("cdninstagram.com" in u or "fbcdn.net" in u)
        and ("t51.71878-15" in u or "t51.2885-15" in u)
        and "rsrc.php" not in u and "static" not in u and "t51.2885-19" not in u and "t51.82787-19" not in u
    ]
    for img_url in imgs:
        try:
            out_path = os.path.join(target_dir, f"{safe_title}.jpg")
            i_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.threads.net/"})
            with urllib.request.urlopen(i_req, timeout=15) as r, open(out_path, "wb") as f:
                f.write(r.read())
            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                return {"success": True, "title": title, "path": out_path, "type": "image"}
        except Exception:
            continue

    return {"success": False, "error": "此貼文為純文字內容，未包含可下載的影片或圖片檔案"}

def build_ydl_options(target_dir: str, quality: str = "best", enable_subtitles: bool = True, browser_cookie: str = None) -> dict:
    os.makedirs(target_dir, exist_ok=True)
    outtmpl = os.path.join(target_dir, "%(title)s [%(id)s].%(ext)s")
    
    opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "windowsfilenames": True,
        "remote_components": ["ejs:github"],
        "retries": 5,
        "fragment_retries": 5,
        "user_agent": USER_AGENT,
    }

    ffmpeg_dir = find_ffmpeg()
    if ffmpeg_dir:
        opts["ffmpeg_location"] = ffmpeg_dir

    if browser_cookie and browser_cookie in ("chrome", "edge", "brave", "firefox"):
        opts["cookiesfrombrowser"] = (browser_cookie, )
    
    if quality == "mp3":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {"key": "FFmpegMetadata"},
            ],
        })
    elif quality == "1080p":
        opts.update({
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegMetadata"}],
        })
    elif quality == "720p":
        opts.update({
            "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegMetadata"}],
        })
    else:  # 'best'
        opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegMetadata"}],
        })
        
    if enable_subtitles and quality != "mp3":
        opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["zh-Hant", "zh-TW", "zh-Hans", "zh", "en"],
            "postprocessor_args": {
                "ffmpeg": ["-c:s", "mov_text"]
            }
        })
        
    return opts

def run_download(url: str, custom_dir: str = None, custom_quality: str = None, task_id: str = None) -> dict:
    cfg = load_config()
    target_dir = custom_dir if (custom_dir and os.path.isdir(custom_dir)) else cfg.get("download_dir")
    quality = custom_quality if custom_quality else cfg.get("quality", "best")
    enable_subs = cfg.get("enable_subtitles", True)
    do_notify = cfg.get("notify", True)
    cookie_setting = cfg.get("browser_cookies", "none")  # Default to none for high stability
    
    clean_url = clean_and_resolve_url(url)
    
    task_info = {
        "id": task_id or f"task_{int(time.time()*1000)}",
        "url": clean_url,
        "title": "正在解析影音資訊...",
        "status": "extracting",
        "progress": 0,
        "speed": "0 KB/秒",
        "eta": "--:--",
        "target_dir": target_dir,
        "quality": quality,
        "file_path": "",
        "error": None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with active_lock:
        active_tasks[task_info["id"]] = task_info
        
    def progress_hook(d):
        with active_lock:
            cur_task = active_tasks.get(task_info["id"])
            if not cur_task:
                return
            if d.get("status") == "downloading":
                cur_task["status"] = "downloading"
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes") or 0
                if total_bytes > 0:
                    cur_task["progress"] = round((downloaded_bytes / total_bytes) * 100, 1)
                
                speed = d.get("speed")
                if speed:
                    if speed > 1024 * 1024:
                        cur_task["speed"] = f"{speed / (1024 * 1024):.1f} MB/秒"
                    else:
                        cur_task["speed"] = f"{speed / 1024:.1f} KB/秒"
                        
                eta = d.get("eta")
                if eta:
                    cur_task["eta"] = f"{int(eta // 60):02d}分{int(eta % 60):02d}秒"
                    
            elif d.get("status") == "finished":
                cur_task["status"] = "processing"
                cur_task["progress"] = 100.0
                cur_task["speed"] = "下載完畢，進行格式合成..."
                if "filename" in d:
                    cur_task["file_path"] = d["filename"]

    # If it's a Threads URL, use dedicated threads extractor
    if "threads.net" in clean_url or "threads.com" in clean_url:
        from .threads_extractor import extract_and_download_threads
        if do_notify:
            notify_start("Threads 影音貼文", clean_url)
            
        def threads_progress(downloaded, total):
            with active_lock:
                if total > 0:
                    task_info["progress"] = round((downloaded / total) * 100, 1)
                    task_info["status"] = "downloading"
                    task_info["speed"] = f"{round(downloaded / (1024*1024), 1)} MB"

        res = extract_and_download_threads(clean_url, target_dir, progress_callback=threads_progress)
        if res.get("success"):
            media_type = res.get("type", "video")
            msg_title = f"{res['title']} (相片)" if media_type == "image" else res["title"]
            with active_lock:
                task_info["title"] = msg_title
                task_info["status"] = "completed"
                task_info["progress"] = 100
                task_info["file_path"] = res["path"]
            add_history_entry({
                "title": msg_title,
                "url": clean_url,
                "path": res["path"],
                "quality": quality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success"
            })
            if do_notify:
                notify_success(msg_title, res["path"], thumbnail_path=res.get("thumbnail") or "")
            return res
        else:
            with active_lock:
                task_info["status"] = "failed"
                task_info["error"] = res["error"]
            add_history_entry({
                "title": "Threads 貼文",
                "url": clean_url,
                "path": "",
                "quality": quality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "failed",
                "error": res["error"]
            })
            if do_notify:
                notify_info("貼文內容提示", res["error"])
            return res

    # Standard yt-dlp path (YouTube, Facebook, Vimeo, IG, TikTok, etc.)
    cookie_candidates = [None]
    if cookie_setting in ("chrome", "edge"):
        cookie_candidates.append(cookie_setting)

    last_error = ""
    for candidate_cookie in cookie_candidates:
        try:
            ydl_opts = build_ydl_options(target_dir, quality, enable_subs, candidate_cookie)
            ydl_opts["progress_hooks"] = [progress_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                video_title = info.get("title", clean_url)
                
                thumbnail_url = info.get("thumbnail") or ""
                with active_lock:
                    task_info["title"] = video_title
                    task_info["status"] = "downloading"
                    
                if do_notify and candidate_cookie == cookie_candidates[0]:
                    notify_start(video_title, clean_url, thumbnail_url=thumbnail_url)
                    
                ydl.download([clean_url])
                
                filename = ydl.prepare_filename(info)
                if quality == "mp3":
                    filename = os.path.splitext(filename)[0] + ".mp3"
                elif not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    if os.path.exists(base + ".mp4"):
                        filename = base + ".mp4"
                    elif os.path.exists(base + ".mkv"):
                        filename = base + ".mkv"
                        
                with active_lock:
                    task_info["status"] = "completed"
                    task_info["progress"] = 100
                    task_info["file_path"] = filename
                    
                add_history_entry({
                    "title": video_title,
                    "url": clean_url,
                    "path": filename,
                    "quality": quality,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success"
                })
                
                if do_notify:
                    notify_success(video_title, filename)
                    
                return {"success": True, "title": video_title, "path": filename}
                
        except Exception as e:
            err_str = str(e)
            last_error = err_str
            # If cookie database is locked by browser, silently skip cookie attempt
            if "cookie database" in err_str.lower() or "sqlite" in err_str.lower():
                continue
            if "login" in err_str.lower() or "unsupported url" in err_str.lower():
                continue
            break

    # If all attempts failed
    clean_error_msg = last_error
    if "unsupported url" in last_error.lower():
        clean_error_msg = "未在此網址中偵測到可下載的影片串流 (該內容可能為純文字、純圖片或受私人權限保護)"
    elif "cookie database" in last_error.lower():
        clean_error_msg = "瀏覽器正在使用中，無法讀取登入 Cookie"

    with active_lock:
        task_info["status"] = "failed"
        task_info["error"] = clean_error_msg
        
    add_history_entry({
        "title": task_info.get("title") or clean_url,
        "url": clean_url,
        "path": "",
        "quality": quality,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "failed",
        "error": clean_error_msg
    })
    
    if do_notify:
        notify_error(task_info.get("title") or "影音下載", clean_error_msg)
        
    return {"success": False, "error": clean_error_msg}

def start_download_async(url: str, custom_dir: str = None, custom_quality: str = None) -> str:
    task_id = f"task_{int(time.time()*1000)}"
    thread = threading.Thread(
        target=run_download,
        args=(url, custom_dir, custom_quality, task_id),
        daemon=True
    )
    thread.start()
    return task_id
