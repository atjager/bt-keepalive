"""
BT Keep-Alive Uninstaller
--------------------------
Stops and removes the BTKeepAlive service and its install directory.
Double-click to run - will self-elevate to Administrator if needed.
"""

import ctypes
import os
import sys
import shutil
import subprocess

SERVICE_NAME = "BTKeepAlive"
INSTALL_DIR = r"C:\Program Files\BTKeepAlive"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


def main():
    if not is_admin():
        print("Administrator rights required - relaunching with elevation...")
        relaunch_as_admin()
        return

    nssm_path = os.path.join(INSTALL_DIR, "nssm.exe")

    if os.path.exists(nssm_path):
        subprocess.run([nssm_path, "stop", SERVICE_NAME], capture_output=True, text=True)
        subprocess.run([nssm_path, "remove", SERVICE_NAME, "confirm"], capture_output=True, text=True)
        print(f"Service '{SERVICE_NAME}' stopped and removed.")
    else:
        print("nssm.exe not found in install directory - service may already be removed.")

    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
        print(f"Removed {INSTALL_DIR}.")

    print("Uninstall complete.")
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
