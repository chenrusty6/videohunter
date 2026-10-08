import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_FILE = BASE_DIR / "history.json"

DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads" / "影速獵手_影片庫")

DEFAULT_CONFIG = {
    "app_name": "影速獵手",
    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "quality": "best",  # 'best' (最高畫質), '1080p', '720p', 'mp3'
    "browser_cookies": "auto",  # 'auto', 'chrome', 'edge', 'none'
    "enable_subtitles": True,
    "notify": True,
    "port": 58231,
    "history_limit": 50
}

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            config = dict(DEFAULT_CONFIG)
            config.update(data)
            return config
    except Exception:
        return dict(DEFAULT_CONFIG)

def save_config(config_data: dict) -> bool:
    try:
        dl_dir = config_data.get("download_dir", DEFAULT_DOWNLOAD_DIR)
        os.makedirs(dl_dir, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def add_history_entry(entry: dict):
    history = get_history()
    history.insert(0, entry)
    cfg = load_config()
    limit = cfg.get("history_limit", 50)
    history = history[:limit]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")
