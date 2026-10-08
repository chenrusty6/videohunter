import sys
import os
import winreg
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
CLI_PATH = BASE_DIR / "cli.py"
ICON_PATH = BASE_DIR / "app.ico"

def get_pythonw_path() -> str:
    local_runtime = BASE_DIR / "runtime" / "pythonw.exe"
    if local_runtime.exists():
        return str(local_runtime)
    py_dir = Path(sys.executable).parent
    pythonw = py_dir / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return sys.executable

def remove_key_tree(root, subkey):
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            info = winreg.QueryInfoKey(key)
            for _ in range(info[0]):
                child = winreg.EnumKey(key, 0)
                remove_key_tree(root, f"{subkey}\\{child}")
        winreg.DeleteKey(root, subkey)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[警告] 移除鍵值 {subkey} 時發生錯誤: {e}")

def uninstall_context_menu():
    print("正在清理舊版右鍵選單項目...")
    old_keys = [
        r"Software\Classes\Directory\Background\shell\VideoDownloader",
        r"Software\Classes\DesktopBackground\shell\VideoDownloader",
        r"Software\Classes\Directory\Background\shell\VideoHunter",
        r"Software\Classes\DesktopBackground\shell\VideoHunter"
    ]
    for k in old_keys:
        remove_key_tree(winreg.HKEY_CURRENT_USER, k)
    print("[OK] 已成功清理右鍵選單！")

def install_context_menu():
    uninstall_context_menu()
    
    pythonw = get_pythonw_path()
    cli = str(CLI_PATH)
    ico = str(ICON_PATH) if ICON_PATH.exists() else "shell32.dll,14"

    # Define menu definitions
    # 1. Folder background sub-menu
    folder_menu_items = [
        ("01_DownloadHere", "下載到此資料夾 (從剪貼簿)", f'"{pythonw}" "{cli}" --clipboard --target-dir "%V"', "shell32.dll,14"),
        ("02_DownloadDefault", "下載到預設儲存位置 (從剪貼簿)", f'"{pythonw}" "{cli}" --clipboard', "shell32.dll,278"),
        ("03_DownloadPick", "自訂位置並下載... (從剪貼簿)", f'"{pythonw}" "{cli}" --clipboard --pick-dir', "shell32.dll,4"),
        ("04_SetDefault", "設定預設儲存位置...", f'"{pythonw}" "{cli}" --set-default-dir', "shell32.dll,315"),
        ("05_Dashboard", "開啟管理控制台", f'"{pythonw}" "{cli}" --open-dashboard', "shell32.dll,15")
    ]

    # 2. Desktop background sub-menu
    desktop_menu_items = [
        ("01_DownloadDefault", "下載到預設儲存位置 (從剪貼簿)", f'"{pythonw}" "{cli}" --clipboard', "shell32.dll,278"),
        ("02_DownloadPick", "自訂位置並下載... (從剪貼簿)", f'"{pythonw}" "{cli}" --clipboard --pick-dir', "shell32.dll,4"),
        ("03_SetDefault", "設定預設儲存位置...", f'"{pythonw}" "{cli}" --set-default-dir', "shell32.dll,315"),
        ("04_Dashboard", "開啟管理控制台", f'"{pythonw}" "{cli}" --open-dashboard', "shell32.dll,15")
    ]

    targets = [
        (r"Software\Classes\Directory\Background\shell\VideoHunter", folder_menu_items),
        (r"Software\Classes\DesktopBackground\shell\VideoHunter", desktop_menu_items)
    ]

    for base_key, items in targets:
        try:
            # Create root cascading item
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key) as k:
                winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "影速獵手")
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, ico)
                winreg.SetValueEx(k, "SubCommands", 0, winreg.REG_SZ, "")

            # Create sub items
            shell_base = f"{base_key}\\shell"
            for sub_name, title, cmd, item_ico in items:
                sub_key = f"{shell_base}\\{sub_name}"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as k:
                    winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, title)
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, item_ico)
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{sub_key}\\command") as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)

            print(f"[OK] 成功註冊階層式右鍵選單: {base_key}")
        except Exception as e:
            print(f"[Error] 註冊失敗 {base_key}: {e}")

    print("\n✅ 「影速獵手」階層式右鍵選單安裝成功！")
    print("👉 在任何資料夾空白處或桌面點擊右鍵，即可展開「影速獵手」子選單！")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall_context_menu()
    else:
        install_context_menu()
