# BT Keep-Alive

Prevents Bluetooth speakers from auto-disconnecting by continuously looping a short, quiet tone through the default Windows playback device - the audio stream never actually closes, which matters for speakers that auto-off when the stream stops rather than on a pure silence timer.

## Files
- `bt_keepalive.py` — background worker, loops `tone.wav` continuously
- `installer.py` — installs as a Windows service via NSSM (self-elevates, bundles NSSM + default tone.wav)
- `uninstall.py` — stops and removes the service
- `generate_tone.py` — standalone, cross-platform (works on macOS) script to generate a custom `tone.wav`
- `.github/workflows/build-windows-exe.yml` — builds all EXEs on push via GitHub Actions (windows-latest runner)

## Build
Push to `main` → check the **Actions** tab → download from the finished run's **Artifacts**:
- `bt_keepalive_installer` → `bt_keepalive_installer.exe` (**ship this one to customers**)
- `bt_keepalive_uninstall` → `bt_keepalive_uninstall.exe`

## Install (on target Windows machine)
1. Set the Bluetooth speaker as the default playback device (Settings → Sound → Output) - usually automatic once paired
2. Double-click `bt_keepalive_installer.exe` → accept UAC prompt
3. Confirm in `services.msc`: **Bluetooth Keep-Alive**, running, auto-start

## Verify
Check `%TEMP%\bt_keepalive.log` (note: if the service runs as Local System, this is `C:\Windows\Temp\bt_keepalive.log`, not your own user's temp folder) — should log `Loop (re)started` at startup and every ~5 min heartbeat.

## Custom tone
On macOS: `python3 generate_tone.py --freq 880 --amplitude 0.15`, then `afplay tone.wav` to preview before uploading. On the target machine, replace `C:\Program Files\BTKeepAlive\tone.wav` with your file, then `nssm restart BTKeepAlive`. The script never regenerates or overwrites this file once it exists, so it persists across restarts and reinstalls.

## Troubleshooting
- **No sound / no log entries:** service runs as Local System by default (Session 0 isolation) and often can't reach the interactive user's audio device. In `services.msc` → Bluetooth Keep-Alive → Log On tab → switch to the logged-in user account, restart the service.
- **Tone audible / too quiet:** tune `TONE_FREQUENCY_HZ` / `TONE_AMPLITUDE` in `bt_keepalive.py`, push, rebuild. Remember it now plays continuously, not in brief bursts, so err quieter than you would for a periodic ping.
- **Speaker still turns off even with continuous playback:** that's a hardware auto-off timer independent of audio activity - no software fix on the source side can prevent it. Confirmed on Blaupunkt PB05DB. Check for an AC-power exemption, or treat the model as unsupported and test an alternative.

## Uninstall
Run `bt_keepalive_uninstall.exe` (also self-elevates) — stops the service, removes it, deletes `C:\Program Files\BTKeepAlive`.
