import re
import ctypes

def get_clipboard_text() -> str:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    # Try up to 5 times in case clipboard is temporarily locked by another app
    for _ in range(5):
        if user32.OpenClipboard(None):
            try:
                CF_UNICODETEXT = 13
                user32.GetClipboardData.restype = ctypes.c_void_p
                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalLock.restype = ctypes.c_wchar_p
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                
                h_mem = user32.GetClipboardData(CF_UNICODETEXT)
                if not h_mem:
                    return ""
                text_ptr = kernel32.GlobalLock(h_mem)
                text = str(text_ptr) if text_ptr else ""
                kernel32.GlobalUnlock(h_mem)
                return text
            finally:
                user32.CloseClipboard()
                return text
        ctypes.windll.kernel32.Sleep(100)
    return ""

def extract_url_from_clipboard() -> str:
    raw = get_clipboard_text().strip()
    if not raw:
        return ""
    # Find http/https url pattern
    match = re.search(r"https?://[^\s\"'<>]+", raw)
    if match:
        return match.group(0)
    # Check if user copied something like vimeo.com/xxx or youtube.com/watch
    if re.search(r"^(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com|twitter\.com|x\.com|facebook\.com|instagram\.com|tiktok\.com|threads\.net|bilibili\.com)", raw, re.IGNORECASE):
        return "https://" + raw
    return ""
