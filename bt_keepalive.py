"""
Bluetooth Speaker Keep-Alive
-----------------------------
Continuously loops a low-volume tone through the default Windows playback
device so the Bluetooth audio stream never actually closes - this prevents
speakers that auto-off based on "stream stopped" (not just "no periodic
audio") from powering down.

Requirements: Windows only (uses winmm.dll via ctypes). No third-party
packages needed - pure standard library.
"""

import wave
import math
import struct
import time
import os
import sys
import ctypes
import tempfile
import logging

# ---- Configuration ----
HEARTBEAT_SECONDS = 300     # safety net: re-assert the loop this often in case playback ever stops
TONE_FREQUENCY_HZ = 880     # audible tone (A5) - swap lower/quieter once confirmed working
TONE_DURATION_MS = 150      # length of one loop cycle
TONE_AMPLITUDE = 0.15       # fraction of max volume (0.0-1.0)
SAMPLE_RATE = 44100
LOG_FILE = os.path.join(tempfile.gettempdir(), "bt_keepalive.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

winmm = ctypes.windll.winmm
SND_FILENAME = 0x00020000
SND_ASYNC = 0x00000001
SND_LOOP = 0x00000008
SND_PURGE = 0x00000040


def generate_tone_wav(path):
    """Write a short low-amplitude sine tone WAV with fade in/out (avoids an audible click at loop points)."""
    n_samples = int(SAMPLE_RATE * TONE_DURATION_MS / 1000)
    fade_samples = max(1, int(n_samples * 0.1))
    max_amp = int(32767 * TONE_AMPLITUDE)

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLE_RATE)

        frames = bytearray()
        for i in range(n_samples):
            fade = min(i / fade_samples, (n_samples - i) / fade_samples, 1.0)
            sample = int(max_amp * fade * math.sin(2 * math.pi * TONE_FREQUENCY_HZ * i / SAMPLE_RATE))
            frames += struct.pack("<h", sample)
        wf.writeframes(bytes(frames))


def start_loop(path):
    """Start (or restart) looping playback. Non-blocking - returns immediately."""
    ok = winmm.PlaySoundW(path, None, SND_FILENAME | SND_ASYNC | SND_LOOP)
    if not ok:
        raise RuntimeError("PlaySoundW loop failed to start")


def stop_loop():
    winmm.PlaySoundW(None, None, SND_PURGE)


def main():
    # Fixed, permanent path - never generated or overwritten by this script
    # once it exists. Replace it directly on disk with any custom .wav you
    # want looped; restart the service to pick up the change.
    tone_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "tone.wav")

    if not os.path.exists(tone_path):
        logging.error("tone.wav not found at %s - generating a default fallback tone.", tone_path)
        generate_tone_wav(tone_path)

    logging.info("Keep-alive started in continuous-loop mode. tone_path=%s", tone_path)
    print(f"Bluetooth keep-alive running (continuous loop). Logging to {LOG_FILE}. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                start_loop(tone_path)
                logging.info("Loop (re)started.")
            except Exception as e:
                logging.error("Failed to start loop: %s", e)
            # Re-assert periodically as a safety net (e.g. in case the audio
            # session ever gets torn down externally) - this does NOT stop
            # and restart the stream in the gap-prone way the old periodic
            # version did, since PlaySoundW with SND_LOOP keeps playing
            # continuously in between these checks.
            time.sleep(HEARTBEAT_SECONDS)
    except KeyboardInterrupt:
        stop_loop()
        logging.info("Keep-alive stopped by user.")
        print("Stopped.")


if __name__ == "__main__":
    main()

# -----------------------------------------------------------------------
# NOTES
# -----------------------------------------------------------------------
# - Continuous looping (not periodic pinging) is required for speakers that
#   auto-off based on the Bluetooth audio STREAM closing, rather than a
#   pure "no audio for N minutes" timer. If your speaker turns off even
#   while something else is actively playing continuously, no software fix
#   on the source side will help - that's a hardware timer independent of
#   stream state.
# - TONE_AMPLITUDE is relative to system volume - test at the actual volume
#   level your customers will run.
# - Because this now plays continuously rather than briefly every few
#   minutes, keep the tone SHORT and QUIET - it's audible for the entire
#   time the service runs, not just in brief bursts.
