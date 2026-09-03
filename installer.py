"""
BT Keep-Alive Installer
------------------------
Installs the Bluetooth keep-alive tool as a Windows service using NSSM.
Double-click to run - it will prompt for admin elevation (UAC) automatically
if not already running as Administrator.

Bundled resources (via PyInstaller --add-binary) are expected next to this
script when unfrozen, or inside sys._MEIPASS when frozen into an exe:
  - bt_keepalive.exe
  - nssm.exe
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


def resource_path(name):
    # When frozen by PyInstaller, bundled files live in sys._MEIPASS.
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def run(cmd):
    print("> " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    return result


def main():
    if not is_admin():
        print("Administrator rights required - relaunching with elevation...")
        relaunch_as_admin()
        return

    print(f"Installing to {INSTALL_DIR} ...")
    os.makedirs(INSTALL_DIR, exist_ok=True)

    keepalive_dst = os.path.join(INSTALL_DIR, "bt_keepalive.exe")
    nssm_dst = os.path.join(INSTALL_DIR, "nssm.exe")

    shutil.copy2(resource_path("bt_keepalive.exe"), keepalive_dst)
    shutil.copy2(resource_path("nssm.exe"), nssm_dst)

    # Clean up any previous install (ignore errors if the service doesn't exist yet)
    run([nssm_dst, "stop", SERVICE_NAME])
    run([nssm_dst, "remove", SERVICE_NAME, "confirm"])

    run([nssm_dst, "install", SERVICE_NAME, keepalive_dst])
    run([nssm_dst, "set", SERVICE_NAME, "DisplayName", "Bluetooth Keep-Alive"])
    run([nssm_dst, "set", SERVICE_NAME, "Description",
         "Periodically plays a quiet tone to prevent Bluetooth speaker auto-disconnect."])
    run([nssm_dst, "set", SERVICE_NAME, "Start", "SERVICE_AUTO_START"])
    run([nssm_dst, "set", SERVICE_NAME, "AppExit", "Default", "Restart"])
    run([nssm_dst, "set", SERVICE_NAME, "AppRestartDelay", "10000"])

    result = run([nssm_dst, "start", SERVICE_NAME])

    print()
    if result.returncode == 0:
        print(f"Done - '{SERVICE_NAME}' service is installed and running.")
    else:
        print("Service was installed but may not have started cleanly - check services.msc.")

    print()
    print("NOTE: the service runs under the Local System account by default. If the")
    print("keep-alive tone doesn't play (check %TEMP%\\bt_keepalive.log on the target")
    print("user's profile), open services.msc, find 'Bluetooth Keep-Alive', and change")
    print("its Log On account to the interactive user so it can reach the default")
    print("audio device.")
    print()
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
