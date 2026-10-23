import os
import sys
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import threading
import sys
import webbrowser
from core.platform_support import RESOURCE_DIR, open_folder

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.config_mgr import load_config, save_config, get_history
from core.downloader import start_download_async, active_tasks, active_lock
from core.clipboard import extract_url_from_clipboard

STATIC_DIR = RESOURCE_DIR / "static"

def is_allowed_origin(origin: str) -> bool:
    """資安防護：僅允許瀏覽器擴充功能與本機同源請求，阻擋外部惡意網頁進行 CSRF / 本地 RPC 跨域攻擊"""
    if not origin:
        return True  # 本機腳本、桌面捷徑或無 Origin 標頭之原生調用
    origin_lower = origin.lower()
    if (origin_lower.startswith("chrome-extension://") or 
        origin_lower.startswith("moz-extension://") or
        origin_lower.startswith("edge-extension://")):
        return True
    try:
        parsed = urllib.parse.urlparse(origin_lower)
        if parsed.hostname in ("127.0.0.1", "localhost"):
            return True
    except Exception:
        pass
    return False

class VideoDownloaderHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # 嚴格 CORS 策略：僅對合法來源反射 Access-Control-Allow-Origin
        origin = self.headers.get("Origin", "")
        if origin and is_allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Credentials", "true")
        super().end_headers()

    def do_OPTIONS(self):
        origin = self.headers.get("Origin", "")
        if origin and not is_allowed_origin(origin):
            self.send_response(403)
            super().end_headers()
            return
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        origin = self.headers.get("Origin", "")
        if origin and not is_allowed_origin(origin):
            self._send_json({"status": "error", "message": "Forbidden Origin (跨域安全攔截)"}, 403)
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/platform':
            self._send_json({'platform': sys.platform, 'windows_menu': sys.platform == 'win32',
                             'can_shutdown': getattr(self.server, 'can_shutdown', False)})
            return
        elif path == "/api/config":
            self._send_json(load_config())
            return
        elif path == "/api/tasks":
            with active_lock:
                tasks = list(active_tasks.values())
            self._send_json({"tasks": tasks})
            return
        elif path == "/api/history":
            self._send_json({"history": get_history()})
            return
        elif path == "/api/open-folder":
            cfg = load_config()
            folder = cfg.get("download_dir", "")
            if os.path.exists(folder):
                open_folder(folder)
                self._send_json({"status": "ok", "message": "Opened folder"})
            else:
                self._send_json({"status": "error", "message": "Folder does not exist"}, 404)
            return

        # Serve UI static files
        if path == "/" or path == "/index.html":
            file_path = STATIC_DIR / "index.html"
            self._serve_file(file_path, "text/html; charset=utf-8")
            return
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = (STATIC_DIR / urllib.parse.unquote(rel_path)).resolve()
            if not file_path.is_relative_to(STATIC_DIR.resolve()):
                self._send_json({'status': 'error', 'message': 'Forbidden path'}, 403)
                return
            if file_path.exists() and file_path.is_file():
                content_type = "application/octet-stream"
                if file_path.suffix == ".css":
                    content_type = "text/css; charset=utf-8"
                elif file_path.suffix == ".js":
                    content_type = "application/javascript; charset=utf-8"
                elif file_path.suffix == ".png":
                    content_type = "image/png"
                elif file_path.suffix == ".svg":
                    content_type = "image/svg+xml"
                self._serve_file(file_path, content_type)
                return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        origin = self.headers.get("Origin", "")
        if origin and not is_allowed_origin(origin):
            self._send_json({"status": "error", "message": "Forbidden Origin (跨域安全攔截)"}, 403)
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if path == "/api/download":
            url = data.get("url", "").strip()
            if not url:
                self._send_json({"status": "error", "message": "網址不能為空"}, 400)
                return
            
            custom_dir = data.get("folder")
            if data.get("pick_folder"):
                from cli import choose_folder_dialog
                cfg = load_config()
                chosen = choose_folder_dialog(
                    title="影速獵手 · 請選擇本次影片下載存放資料夾",
                    initial_dir=cfg.get("download_dir")
                )
                if not chosen or not os.path.isdir(chosen):
                    self._send_json({"status": "canceled", "message": "已取消選擇資料夾"})
                    return
                custom_dir = chosen

            task_id = start_download_async(
                url=url,
                custom_dir=custom_dir,
                custom_quality=data.get("quality")
            )
            self._send_json({"status": "ok", "task_id": task_id, "message": "已加入下載佇列"})
            return

        elif path == "/api/clipboard":
            url = extract_url_from_clipboard()
            if not url:
                self._send_json({"status": "error", "message": "剪貼簿內未偵測到影片網址"}, 400)
                return
            task_id = start_download_async(url=url)
            self._send_json({"status": "ok", "task_id": task_id, "url": url, "message": "成功讀取剪貼簿並開始下載"})
            return

        elif path == "/api/config":
            cfg = load_config()
            for k in ["download_dir", "quality", "browser_cookies", "enable_subtitles", "notify"]:
                if k in data:
                    cfg[k] = data[k]
            save_config(cfg)
            self._send_json({"status": "ok", "config": cfg})
            return

        elif path == "/api/browse-dir":
            from cli import choose_folder_dialog
            cfg = load_config()
            chosen = choose_folder_dialog(
                title="影速獵手 · 請選擇預設儲存資料夾",
                initial_dir=cfg.get("download_dir")
            )
            if chosen and os.path.isdir(chosen):
                cfg["download_dir"] = chosen
                save_config(cfg)
                self._send_json({"status": "ok", "path": chosen})
            else:
                self._send_json({"status": "canceled", "path": cfg.get("download_dir")})
            return

        elif path == "/api/reinstall-menu":
            if sys.platform != 'win32':
                self._send_json({'status': 'error', 'message': '此功能僅適用 Windows；Mac 可使用瀏覽器擴充套件。'}, 400)
                return
            from setup_right_click import install_context_menu
            try:
                install_context_menu()
                self._send_json({"status": "ok", "message": "右鍵選單註冊成功"})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
            return

        elif path == '/api/shutdown' and getattr(self.server, 'can_shutdown', False):
            self._send_json({'status': 'ok'})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, data: dict, code: int = 200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_file(self, file_path: Path, content_type: str):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def log_message(self, format, *args):
        # Quiet logger to keep terminal clean
        pass

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_server(port=None, launch_browser=False, can_shutdown=False):
    cfg = load_config()
    server_port = port if port is not None else cfg.get("port", 58231)
    server_address = ("127.0.0.1", server_port)
    httpd = HTTPServer(server_address, VideoDownloaderHandler)
    httpd.can_shutdown = can_shutdown
    if launch_browser:
        threading.Thread(target=webbrowser.open, args=(f'http://127.0.0.1:{httpd.server_port}/',), daemon=True).start()
    print(f"[OK] [VideoHunter] 後台服務已啟動: http://127.0.0.1:{httpd.server_port}")
    print(f"[OK] 管理主頁面: http://127.0.0.1:{server_port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服務...")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
