import os
import re
import json
import urllib.request
from pathlib import Path

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

def is_threads_url(url: str) -> bool:
    return "threads.net" in url or "threads.com" in url

def extract_and_download_threads(url: str, target_dir: str, progress_callback=None) -> dict:
    os.makedirs(target_dir, exist_ok=True)
    clean_url = url.replace("threads.com", "threads.net")
    # Clean tracking query
    clean_url = re.sub(r"([?&])(?:xmt|sjid|igsh|utm_[^&]+)=[^&]*", "", clean_url).rstrip("?&")

    req = urllib.request.Request(clean_url, headers=BROWSER_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {"success": False, "error": f"無法載入 Threads 貼文: {e}"}

    # Extract title
    t_m = re.search(r"<title>([^<]+)</title>", html)
    raw_title = t_m.group(1).replace(" | Threads", "").strip() if t_m else "Threads 影片"
    clean_title = re.sub(r'[\r\n\t\\/*?:"<>|]', " ", raw_title)
    clean_title = " ".join(clean_title.split())[:45].strip() or "Threads_Video"

    # Find JSON data in data-sjs scripts
    scripts = re.findall(r'<script[^>]*data-sjs[^>]*>(.*?)</script>', html)
    vids = []
    imgs = []

    def recursive_find(obj):
        if isinstance(obj, dict):
            if "video_versions" in obj and isinstance(obj["video_versions"], list):
                for item in obj["video_versions"]:
                    if isinstance(item, dict) and item.get("url"):
                        vids.append(item)
            if "image_versions2" in obj and isinstance(obj["image_versions2"], dict):
                candidates = obj["image_versions2"].get("candidates", [])
                if candidates and isinstance(candidates[0], dict) and candidates[0].get("url"):
                    imgs.append(candidates[0])
            for val in obj.values():
                recursive_find(val)
        elif isinstance(obj, list):
            for item in obj:
                recursive_find(item)

    for s in scripts:
        try:
            data = json.loads(s)
            recursive_find(data)
        except Exception:
            continue

    # 1. Download best video if available
    if vids:
        # Sort by resolution (width * height) descending
        def get_res(v):
            w = v.get("width") or 0
            h = v.get("height") or 0
            return w * h
        
        sorted_vids = sorted(vids, key=get_res, reverse=True)
        best_vid = sorted_vids[0]
        vid_url = best_vid["url"]
        
        out_file = os.path.join(target_dir, f"{clean_title}.mp4")
        thumb_url = imgs[0]["url"] if imgs else ""

        try:
            v_req = urllib.request.Request(vid_url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.threads.net/"})
            with urllib.request.urlopen(v_req, timeout=20) as resp, open(out_file, "wb") as f:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 65536
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)

            return {
                "success": True,
                "title": raw_title,
                "path": out_file,
                "type": "video",
                "thumbnail": thumb_url
            }
        except Exception as e:
            return {"success": False, "error": f"下載影片串流失敗: {e}"}

    # 2. Download image if it's a photo post
    if imgs:
        best_img = imgs[0]
        img_url = best_img["url"]
        out_file = os.path.join(target_dir, f"{clean_title}.jpg")
        try:
            i_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT, "Referer": "https://www.threads.net/"})
            with urllib.request.urlopen(i_req, timeout=15) as resp, open(out_file, "wb") as f:
                f.write(resp.read())
            return {
                "success": True,
                "title": f"{raw_title} (相片)",
                "path": out_file,
                "type": "image",
                "thumbnail": img_url
            }
        except Exception as e:
            return {"success": False, "error": f"下載相片失敗: {e}"}

    return {"success": False, "error": "此貼文為純文字內容，未包含可下載的影音或相片"}
