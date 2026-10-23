"""Build on native macOS; PyInstaller collects FFmpeg's linked libraries."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    return subprocess.run(list(args), check=True, capture_output=True, text=True).stdout


def main():
    if sys.platform != 'darwin':
        raise SystemExit('Build this app on macOS, not on Windows.')
    os.chdir(ROOT)
    generated = ROOT / 'packaging/generated'
    generated.mkdir(parents=True, exist_ok=True)
    notices = generated / 'licenses'
    notices.mkdir(exist_ok=True)
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get('Name', 'package')
        for entry in distribution.files or []:
            if any(word in str(entry).lower() for word in ('license', 'copying', 'notice')):
                source = distribution.locate_file(entry)
                if source.is_file():
                    target = notices / name / str(entry)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = f'https://raw.githubusercontent.com/python/cpython/v{platform.python_version()}/LICENSE'
    with urllib.request.urlopen(python_license, timeout=30) as response:
        (notices / 'Python-LICENSE.txt').write_bytes(response.read())
    dependencies = ['ffmpeg', *run('brew', 'deps', '--installed', '--formula', 'ffmpeg').split()]
    for dependency in dependencies:
        cellar = Path(run('brew', '--prefix', dependency).strip())
        for relative in ('LICENSE', 'LICENSE.txt', 'COPYING', 'COPYING.txt', 'share/licenses', '.brew'):
            source = cellar / relative
            target = notices / 'Homebrew' / dependency / relative
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            elif source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    assert ffmpeg and ffprobe
    info = {'architecture': platform.machine(), 'macos': platform.mac_ver()[0],
            'python': sys.version, 'ffmpeg': run(ffmpeg, '-version'),
            'homebrew': json.loads(run('brew', 'info', '--json=v2', 'ffmpeg')),
            'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
            'commit': os.environ.get('GITHUB_SHA'), 'developer_id_signed': False, 'notarized': False}
    (generated / 'BUILD_INFO.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--onedir',
            '--name', 'VideoHunter', '--osx-bundle-identifier', 'com.chenrusty6.videohunter',
            '--target-architecture', platform.machine(), '--icon', 'icon.png',
            '--collect-all', 'yt_dlp', '--collect-all', 'curl_cffi', '--collect-all', 'certifi',
            '--copy-metadata', 'yt-dlp', '--add-data', 'static:static', '--add-data', 'icon.png:.',
            '--add-data', 'MAC_README.md:.', '--add-data', 'LICENSE:.',
            '--add-data', 'licenses:licenses/ffmpeg', '--add-data', f'{notices}:licenses/third-party',
            '--add-data', f'{generated / "BUILD_INFO.json"}:.',
            '--add-binary', f'{ffmpeg}:bin', '--add-binary', f'{ffprobe}:bin',
            '--exclude-module', 'tkinter', '--exclude-module', 'winotify', 'mac_app.py']
    subprocess.run(args, check=True)
    app = ROOT / 'dist/VideoHunter.app'
    import plistlib
    plist_path = app / 'Contents/Info.plist'
    with plist_path.open('rb') as stream:
        plist = plistlib.load(stream)
    plist.update(CFBundleShortVersionString='1.1.0-beta.1', CFBundleVersion='1.1.0',
                 CFBundleDisplayName='影速獵手 VideoHunter', NSHighResolutionCapable=True)
    with plist_path.open('wb') as stream:
        plistlib.dump(plist, stream)
    # Info.plist was changed after PyInstaller's ad-hoc signature.
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True)
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    print(f'Built {app} for {platform.machine()}')


if __name__ == '__main__':
    main()
