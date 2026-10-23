"""macOS bundle entry point: open the existing local web interface."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import webbrowser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    from core.platform_support import DATA_DIR, RESOURCE_DIR, ffmpeg_directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if getattr(sys, 'frozen', False):
        log = (DATA_DIR / 'app.log').open('a', encoding='utf-8', buffering=1)
        sys.stdout = sys.stderr = log
    import server
    from core.config_mgr import load_config
    if args.self_test:
        ffmpeg = Path(ffmpeg_directory()) / ('ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg')
        ffprobe = ffmpeg.with_name('ffprobe.exe' if sys.platform == 'win32' else 'ffprobe')
        for binary in (ffmpeg, ffprobe):
            subprocess.run([str(binary), '-version'], check=True, capture_output=True, timeout=15)
        assert (RESOURCE_DIR / 'static/index.html').is_file()
        report = {'status': 'pass', 'platform': sys.platform, 'ffmpeg': str(ffmpeg),
                  'resources': str(RESOURCE_DIR), 'data_dir': str(DATA_DIR)}
        (DATA_DIR / 'self-test.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        return
    port = args.port if args.port is not None else load_config().get('port', 58231)
    url = f'http://127.0.0.1:{port}/'
    # Reopening the same app reuses its service rather than failing on the port.
    try:
        with urllib.request.urlopen(url + 'api/platform', timeout=1) as response:
            info = json.load(response)
        if info.get('can_shutdown'):
            if not args.no_browser:
                webbrowser.open(url)
            return
        raise RuntimeError(f'Port {port} is already used by another service.')
    except OSError:
        pass
    server.run_server(port, launch_browser=not args.no_browser, can_shutdown=True)


if __name__ == '__main__':
    main()
