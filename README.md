# BT Keep-Alive

Prevents Bluetooth speakers from auto-disconnecting after 10-15 min of silence by playing a short, quiet, near-inaudible tone every 8 minutes.

## Files
- `bt_keepalive.py` — background worker, plays the tone on a loop
- `installer.py` — installs `bt_keepalive.exe` as a Windows service via NSSM (self-elevates, bundles NSSM)
- `uninstall.py` — stops and removes the service
- `.github/workflows/build-windows-exe.yml` — builds all EXEs on push via GitHub Actions (windows-latest runner)

## Build
Push to `main` → check the **Actions** tab → download from the finished run's **Artifacts**:
- `bt_keepalive_installer` → `bt_keepalive_installer.exe` (**ship this one to customers**)
- `bt_keepalive_uninstall` → `bt_keepalive_uninstall.exe`

## Install (on target Windows machine)
1. Set the Bluetooth speaker as the default playback device (Settings → Sound → Output)
2. Double-click `bt_keepalive_installer.exe` → accept UAC prompt
3. Confirm in `services.msc`: **Bluetooth Keep-Alive**, running, auto-start

## Verify
Check `%TEMP%\bt_keepalive.log` — should log `Tone played` every ~8 min.

## Troubleshooting
- **No tone / no log entries after install:** service runs as Local System by default, which may lack access to the interactive user's audio device. In `services.msc` → Bluetooth Keep-Alive → Log On tab → switch to the logged-in user account.
- **Tone audible / too quiet:** tune `TONE_FREQUENCY_HZ` / `TONE_AMPLITUDE` in `bt_keepalive.py`, push, rebuild.
- **Speaker still disconnects:** lower `INTERVAL_SECONDS` (must stay under the speaker's actual timeout), or that model may time out regardless of audio activity — flag as unsupported.

## Uninstall
Run `bt_keepalive_uninstall.exe` (also self-elevates) — stops the service, removes it, deletes `C:\Program Files\BTKeepAlive`.
