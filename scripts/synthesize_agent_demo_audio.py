import math
import random
import struct
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 48000
DURATION = 7.0


def envelope(t, center, width):
    x = abs(t - center) / max(width, 1e-6)
    return max(0.0, 1.0 - x)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: synthesize_agent_demo_audio.py OUTPUT_WAV")
    out = Path(sys.argv[1]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(247)
    total = int(DURATION * SAMPLE_RATE)
    footsteps = [0.45, 1.02, 1.58, 2.15, 2.72, 3.28, 3.85, 4.42, 5.0]
    shot = 4.67
    frames = bytearray()
    low_noise = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        # Quiet mechanical room tone.
        hum = (
            0.030 * math.sin(2 * math.pi * 58 * t)
            + 0.016 * math.sin(2 * math.pi * 116 * t)
            + 0.008 * math.sin(2 * math.pi * 232 * t)
        )
        low_noise = low_noise * 0.985 + rng.uniform(-1.0, 1.0) * 0.015
        ambience = hum + 0.010 * low_noise

        step = 0.0
        for st in footsteps:
            e = envelope(t, st, 0.065)
            if e > 0:
                step += e * (
                    0.12 * math.sin(2 * math.pi * 82 * (t - st))
                    + 0.06 * rng.uniform(-1.0, 1.0)
                )

        blast_env = envelope(t, shot, 0.10)
        blast = 0.0
        if blast_env > 0:
            dt = t - shot
            freq = 950 - 620 * min(1.0, max(0.0, dt / 0.10))
            blast = blast_env * (
                0.28 * math.sin(2 * math.pi * freq * dt)
                + 0.15 * rng.uniform(-1.0, 1.0)
            )

        tail = 0.0
        if shot < t < shot + 0.8:
            dt = t - shot
            tail = 0.045 * math.exp(-4.5 * dt) * math.sin(2 * math.pi * 180 * dt)

        mono = max(-0.88, min(0.88, ambience + step + blast + tail))
        # Slight stereo width without shifting timing.
        left = mono
        right = max(-0.88, min(0.88, mono * 0.96 + 0.008 * math.sin(2 * math.pi * 0.7 * t)))
        frames += struct.pack("<hh", int(left * 32767), int(right * 32767))

    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(frames)
    print(out)


if __name__ == "__main__":
    main()
