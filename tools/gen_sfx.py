"""Generate the game's sound effects as 16-bit mono WAV files.

Standard library only, so the project keeps its single pygame dependency.
Output is deterministic: running this twice produces byte-identical files.
"""

import math
import random
import wave
from array import array
from pathlib import Path

SAMPLE_RATE = 22050
AMPLITUDE = 0.34
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"


def square(phase: float, duty: float = 0.5) -> float:
    return 1.0 if (phase % 1.0) < duty else -1.0


def triangle(phase: float) -> float:
    return 4.0 * abs((phase % 1.0) - 0.5) - 1.0


def envelope(index: int, total: int, attack: float, release: float) -> float:
    if attack > 0.0:
        attack_gain = min(1.0, (index / SAMPLE_RATE) / attack)
    else:
        attack_gain = 1.0
    return attack_gain * math.exp(-(index / total) / release)


def sweep(
    duration: float,
    start_hz: float,
    end_hz: float,
    wave_fn,
    duty: float = 0.5,
    attack: float = 0.004,
    release: float = 0.3,
) -> array:
    total = int(SAMPLE_RATE * duration)
    out = array("h", bytes(2 * total))
    phase = 0.0
    for i in range(total):
        t = i / total
        freq = start_hz + (end_hz - start_hz) * t
        phase += freq / SAMPLE_RATE
        if wave_fn is square:
            value = square(phase, duty)
        else:
            value = wave_fn(phase)
        out[i] = int(AMPLITUDE * 32767 * value * envelope(i, total, attack, release))
    return out


def noise_hit(
    duration: float, start_hz: float, end_hz: float, seed: int, release: float = 0.18
) -> array:
    total = int(SAMPLE_RATE * duration)
    out = array("h", bytes(2 * total))
    rng = random.Random(seed)
    phase = 0.0
    low = 0.0
    for i in range(total):
        t = i / total
        freq = start_hz + (end_hz - start_hz) * t
        phase += freq / SAMPLE_RATE
        raw = 0.6 * square(phase, 0.5) + 0.4 * rng.uniform(-1.0, 1.0)
        low += 0.35 * (raw - low)
        out[i] = int(AMPLITUDE * 32767 * low * envelope(i, total, 0.002, release))
    return out


def arpeggio(notes: list[float], note_seconds: float, duty: float = 0.5) -> array:
    per_note = int(SAMPLE_RATE * note_seconds)
    out = array("h")
    for index, hz in enumerate(notes):
        phase = 0.0
        for i in range(per_note):
            phase += hz / SAMPLE_RATE
            decay = math.exp(-(i / per_note) / 0.55)
            level = AMPLITUDE * (0.55 + 0.45 * decay) * (1.0 if index % 2 == 0 else 0.8)
            out.append(int(level * 32767 * square(phase, duty)))
    return out


def write_wav(name: str, samples: array) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.wav"
    clipped = array("h", (max(-32768, min(32767, s)) for s in samples))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(clipped.tobytes())
    return path


SOUNDS = {
    "jump": lambda: sweep(0.14, 210.0, 620.0, square, duty=0.5, release=0.32),
    "land": lambda: sweep(0.10, 170.0, 62.0, triangle, release=0.22),
    "hazard": lambda: noise_hit(0.22, 420.0, 110.0, seed=20260926),
    "portal": lambda: arpeggio([523.25, 659.25, 783.99, 1046.5], 0.07),
    "ui": lambda: sweep(0.045, 1046.5, 880.0, square, duty=0.25, release=0.16),
}


def main() -> None:
    for name, build in SOUNDS.items():
        path = write_wav(name, build())
        seconds = path.stat().st_size / (SAMPLE_RATE * 2)
        print(f"{path.relative_to(OUT_DIR.parent.parent)}  {seconds:.3f}s")


if __name__ == "__main__":
    main()
