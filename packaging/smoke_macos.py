"""Exercise the real frozen app, not only imports or mock platform adapters."""
import functools
import http.server
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent


def main():
    app = Path(sys.argv[1]).resolve()
    binary = app / 'Contents/MacOS/VideoHunter'
    assert binary.is_file(), binary
    generated = ROOT / 'packaging/generated'
    generated.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='videohunter-mac-') as temp:
        working = Path(temp)
        data = working / 'data'
        downloads = working / 'downloads'
        env = dict(os.environ, VIDEOHUNTER_DATA_DIR=str(data), VIDEOHUNTER_DOWNLOAD_DIR=str(downloads),
                   PATH='/usr/bin:/bin:/usr/sbin:/sbin', PYTHONDONTWRITEBYTECODE='1')
        # No Homebrew or build Python on PATH; tools must be inside the app.
        subprocess.run([str(binary), '--self-test'], env=env, check=True, timeout=60)
        self_test = json.loads((data / 'self-test.json').read_text())
        ffmpeg = Path(self_test['ffmpeg'])
        ffprobe = ffmpeg.with_name('ffprobe')
        assert ffmpeg.is_relative_to(app), ffmpeg
        assert ffprobe.is_file()
        for tool in (ffmpeg, ffprobe):
            linked = subprocess.run(['/usr/bin/otool', '-L', str(tool)], capture_output=True, text=True, check=True).stdout
            assert '/opt/homebrew/' not in linked and '/usr/local/Cellar/' not in linked, linked
        fixture = working / 'fixture.mp4'
        subprocess.run([str(ffmpeg), '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=160x90:r=10',
                        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '1',
                        '-c:v', 'mpeg4', '-c:a', 'aac', '-shortest', str(fixture)],
                       env=env, check=True, capture_output=True, timeout=30)

        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *_):
                pass
        fixture_server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=working))
        threading.Thread(target=fixture_server.serve_forever, daemon=True).start()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen([str(binary), '--port', str(port), '--no-browser'], env=env)
        base = f'http://127.0.0.1:{port}'

        def request(path, body=None, origin=None):
            headers = {}
            payload = None
            if body is not None:
                payload = json.dumps(body).encode()
                headers['Content-Type'] = 'application/json'
            if origin:
                headers['Origin'] = origin
            query = urllib.request.Request(base + path, data=payload, headers=headers)
            with urllib.request.urlopen(query, timeout=10) as response:
                raw = response.read()
                return json.loads(raw) if 'json' in response.headers.get('Content-Type', '') else raw
        try:
            deadline = time.monotonic() + 45
            while True:
                try:
                    capability = request('/api/platform')
                    break
                except OSError:
                    if process.poll() is not None or time.monotonic() > deadline:
                        log = (data / 'app.log').read_text() if (data / 'app.log').exists() else ''
                        raise AssertionError(f'App did not start: {process.poll()}\n{log}')
                    time.sleep(.3)
            assert capability['platform'] == 'darwin' and not capability['windows_menu']
            assert b'VideoHunter' in request('/')
            assert b'btnQuitApp' in request('/static/app.js')
            try:
                request('/static/%2e%2e/config.json')
                raise AssertionError('Static traversal must be rejected.')
            except urllib.error.HTTPError as error:
                assert error.code == 403
            try:
                request('/api/config', origin='https://untrusted.example')
                raise AssertionError('External origin must be rejected.')
            except urllib.error.HTTPError as error:
                assert error.code == 403
            assert request('/api/config', {'notify': False, 'enable_subtitles': False})['status'] == 'ok'
            fixture_url = f'http://127.0.0.1:{fixture_server.server_port}/fixture.mp4'
            outputs = []
            for quality in ('best', 'mp3'):
                job = request('/api/download', {'url': fixture_url, 'quality': quality})
                assert job['status'] == 'ok', job
                deadline = time.monotonic() + 90
                while True:
                    tasks = request('/api/tasks')['tasks']
                    task = next(t for t in tasks if t['id'] == job['task_id'])
                    if task['status'] in ('completed', 'failed'):
                        break
                    assert time.monotonic() < deadline, task
                    time.sleep(.25)
                assert task['status'] == 'completed', task
                output = Path(task['file_path'])
                assert output.is_file() and output.stat().st_size > 0, task
                probe = subprocess.run([str(ffprobe), '-v', 'error', '-show_entries', 'format=duration',
                                        '-of', 'json', str(output)], env=env, capture_output=True, text=True, check=True)
                assert float(json.loads(probe.stdout)['format']['duration']) > .5
                outputs.append({'quality': quality, 'bytes': output.stat().st_size, 'extension': output.suffix})
            assert len(request('/api/history')['history']) == 2
            assert request('/api/shutdown', {})['status'] == 'ok'
            process.wait(timeout=15)
            assert process.returncode == 0
            report = {'status': 'pass', 'architecture': platform.machine(), 'macos': platform.mac_ver()[0],
                      'native_app_started': True, 'requires_host_python': False, 'requires_host_ffmpeg': False,
                      'http_ui': True, 'data_storage': True, 'local_downloads': outputs,
                      'external_origin_rejected': True, 'static_path_escape_rejected': True,
                      'shutdown': True, 'finder_double_click_tested': False,
                      'live_websites_tested': False, 'developer_id_signed': False, 'notarized': False}
            (generated / 'smoke-test.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps(report, indent=2))
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
            fixture_server.shutdown()
            fixture_server.server_close()
            if (data / 'app.log').exists():
                (generated / 'app-smoke.log').write_text((data / 'app.log').read_text(), encoding='utf-8')


if __name__ == '__main__':
    main()
