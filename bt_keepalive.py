"""
Bluetooth Speaker Keep-Alive
-----------------------------
Periodically plays a very short, low-volume, high-frequency tone through the
default Windows playback device to prevent Bluetooth speakers from
auto-disconnecting due to inactivity/idle timeouts.

Requirements: Windows only (uses winmm.dll via ctypes). No third-party
packages needed - pure standard library.

Tune TONE_FREQUENCY_HZ / TONE_AMPLITUDE / INTERVAL_SECONDS to taste - see
notes at the bottom of this file.
"""

import wave
import math
import struct
import time
import tempfile
import os
import ctypes
import logging

# ---- Configuration ----
INTERVAL_SECONDS = 480      # ping every 8 min (< typical 10-15 min auto-off timeout)
TONE_FREQUENCY_HZ = 18500   # near-ultrasonic; inaudible to most adults, some kids/pets may hear it
TONE_DURATION_MS = 150      # very short blip
TONE_AMPLITUDE = 0.03       # fraction of max volume (0.0-1.0) - keep LOW, tune per deployment
SAMPLE_RATE = 44100
LOG_FILE = os.path.join(tempfile.gettempdir(), "bt_keepalive.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def generate_tone_wav(path):
    """Write a short low-amplitude sine tone WAV with fade in/out (avoids an audible click)."""
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


def play_wav(path):
    """Play synchronously via winmm so we know it actually finished (and errors surface)."""
    winmm = ctypes.windll.winmm
    SND_FILENAME = 0x00020000
    SND_SYNC = 0x00000000
    ok = winmm.PlaySoundW(path, None, SND_FILENAME | SND_SYNC)
    if not ok:
        raise RuntimeError("PlaySoundW returned failure")


def main():
    tone_path = os.path.join(tempfile.gettempdir(), "bt_keepalive_tone.wav")
    generate_tone_wav(tone_path)
    logging.info(
        "Keep-alive started. interval=%ss freq=%sHz amplitude=%s",
        INTERVAL_SECONDS, TONE_FREQUENCY_HZ, TONE_AMPLITUDE,
    )
    print(f"Bluetooth keep-alive running. Logging to {LOG_FILE}. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                play_wav(tone_path)
                logging.info("Tone played.")
            except Exception as e:
                logging.error("Failed to play tone: %s", e)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logging.info("Keep-alive stopped by user.")
        print("Stopped.")


if __name__ == "__main__":
    main()

# -----------------------------------------------------------------------
# NOTES
# -----------------------------------------------------------------------
# - This works by playing REAL (short, quiet) audio, not silence - most
#   speaker firmware resets its idle timer on any actual audio stream,
#   which is why a true silent loop is unreliable across brands.
# - TONE_FREQUENCY_HZ near 18-19kHz is inaudible to most adults but some
#   younger people, and most dogs/cats, can still hear it. If that's a
#   problem, drop to a very quiet audible tone (e.g. 200-400Hz) instead -
#   trade-off is it's technically audible but very brief and quiet.
# - TONE_AMPLITUDE is relative to the system's current output volume, so
#   if a customer runs their system volume very high, "3%" may still be
#   noticeable. Test on the actual hardware you ship with.
# - INTERVAL_SECONDS should be safely under the shortest timeout you've
#   observed across your supported speaker models - 8 min is a
#   conservative default for a 10-15 min window.
# - This only helps for speakers where "no audio stream" triggers the
#   auto-off. A few speakers time out based on total elapsed time
#   regardless of pings - those need a documented "known incompatible"
#   list instead.
