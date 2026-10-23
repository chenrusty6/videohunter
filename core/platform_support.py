"""Native desktop operations, with writable data outside a macOS app bundle."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

PLATFORM = sys.platform
RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
DATA_DIR = Path(os.environ.get('VIDEOHUNTER_DATA_DIR') or (
    Path.home() / 'Library' / 'Application Support' / 'VideoHunter'
    if PLATFORM == 'darwin' else RESOURCE_DIR
))


def ffmpeg_directory() -> str:
    name = 'ffmpeg.exe' if PLATFORM == 'win32' else 'ffmpeg'
    candidates = [RESOURCE_DIR / 'bin' / name]
    if PLATFORM == 'darwin':
        candidates.extend([Path('/opt/homebrew/bin/ffmpeg'), Path('/usr/local/bin/ffmpeg')])
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.parent)
    found = shutil.which(name)
    return str(Path(found).parent) if found else ''


def open_folder(folder: str):
    if PLATFORM == 'darwin':
        subprocess.run(['/usr/bin/open', folder], check=True, timeout=10)
    elif PLATFORM == 'win32':
        os.startfile(folder)
    else:
        subprocess.run(['xdg-open', folder], check=True, timeout=10)


def mac_clipboard() -> str:
    try:
        return subprocess.run(['/usr/bin/pbpaste'], capture_output=True,
                              text=True, encoding='utf-8', check=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return ''


def mac_choose_folder(title: str) -> str:
    # Pass all user-controlled strings as argv; never interpolate AppleScript.
    script = '''on run argv
try
set chosen to choose folder with prompt (item 1 of argv)
return POSIX path of chosen
on error number -128
return ""
end try
end run'''
    try:
        return subprocess.run(['/usr/bin/osascript', '-e', script, title],
                              capture_output=True, text=True, encoding='utf-8',
                              check=True, timeout=300).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def mac_notification(title: str, message: str):
    script = '''on run argv
display notification (item 2 of argv) with title (item 1 of argv)
end run'''
    try:
        subprocess.run(['/usr/bin/osascript', '-e', script, title, message],
                       capture_output=True, check=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass  # Notifications must never interrupt a download.
