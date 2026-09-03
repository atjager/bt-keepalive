"""
Generate a short keep-alive tone WAV file.

Runs anywhere (macOS, Windows, Linux) with plain python3 - no dependencies,
uses only the standard library. Run it, then upload the resulting tone.wav
to the target Windows machine.

Usage:
    python3 generate_tone.py
    python3 generate_tone.py --freq 880 --amplitude 0.15 --duration 150 --out tone.wav
"""

import argparse
import wave
import math
import struct

SAMPLE_RATE = 44100


def generate_tone_wav(path, frequency_hz, duration_ms, amplitude):
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    fade_samples = max(1, int(n_samples * 0.1))
    max_amp = int(32767 * amplitude)

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLE_RATE)

        frames = bytearray()
        for i in range(n_samples):
            fade = min(i / fade_samples, (n_samples - i) / fade_samples, 1.0)
            sample = int(max_amp * fade * math.sin(2 * math.pi * frequency_hz * i / SAMPLE_RATE))
            frames += struct.pack("<h", sample)
        wf.writeframes(bytes(frames))


def main():
    parser = argparse.ArgumentParser(description="Generate a short tone WAV for the BT keep-alive service.")
    parser.add_argument("--freq", type=float, default=880, help="Tone frequency in Hz (default: 880, audible A5)")
    parser.add_argument("--amplitude", type=float, default=0.15, help="Volume as a fraction 0.0-1.0 (default: 0.15)")
    parser.add_argument("--duration", type=int, default=150, help="Duration in milliseconds (default: 150)")
    parser.add_argument("--out", type=str, default="tone.wav", help="Output file path (default: tone.wav)")
    args = parser.parse_args()

    generate_tone_wav(args.out, args.freq, args.duration, args.amplitude)
    print(f"Wrote {args.out}  (freq={args.freq}Hz, amplitude={args.amplitude}, duration={args.duration}ms)")


if __name__ == "__main__":
    main()
