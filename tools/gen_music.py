"""Generate the game's chiptune loops as 16-bit mono WAV files.

Standard library only, matching tools/gen_sfx.py, so the project keeps its
single pygame dependency. Output is deterministic: running this twice
produces byte-identical files.

Every track spans a whole number of bars and each note decays to silence
before the loop point, so wrapping from the last sample back to the first
is continuous and the result loops without a click.
"""

import math
import wave
from array import array
from pathlib import Path

SAMPLE_RATE = 22050
PEAK = 0.80
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"
REST = None


def hz(midi: float) -> float:
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def square(phase: float, duty: float = 0.5) -> float:
    return 1.0 if (phase % 1.0) < duty else -1.0


def triangle(phase: float) -> float:
    return 4.0 * abs((phase % 1.0) - 0.5) - 1.0


def render(pattern, seconds_per_beat, wave_fn, gain, duty=0.5, decay=3.0):
    out: list[float] = []
    for midi, beats in pattern:
        total = max(1, int(round(beats * seconds_per_beat * SAMPLE_RATE)))
        if midi is REST:
            out.extend([0.0] * total)
            continue
        step = hz(midi) / SAMPLE_RATE
        phase = 0.0
        for i in range(total):
            t = i / SAMPLE_RATE
            env = min(1.0, t / 0.008) * math.exp(-t * decay)
            value = square(phase, duty) if wave_fn is square else wave_fn(phase)
            out.append(value * env * gain)
            phase += step
    return out


def mix(*voices) -> list[float]:
    length = max((len(voice) for voice in voices), default=0)
    out = [0.0] * length
    for voice in voices:
        for index, sample in enumerate(voice):
            out[index] += sample
    return out


def normalize(samples, peak=PEAK):
    high = max((abs(sample) for sample in samples), default=0.0)
    if high == 0.0:
        return samples
    scale = peak / high
    return [sample * scale for sample in samples]


def fade_tail(samples, seconds=0.04):
    """Force the loop boundary to silence so the wrap cannot click."""
    count = int(seconds * SAMPLE_RATE)
    if count <= 0 or count >= len(samples):
        return samples
    out = list(samples)
    for offset in range(count):
        out[len(out) - count + offset] *= 1.0 - (offset / count)
    return out


def write_wav(name: str, samples) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.wav"
    clipped = array("h", (max(-32768, min(32767, int(s * 32767))) for s in samples))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(clipped.tobytes())
    return path


def eighths(notes) -> list[tuple[float, float]]:
    return [(midi, 0.5) for midi in notes]


MENU_BPM = 96.0
MENU_BASS = [
    (45, 2.0), (45, 2.0),
    (41, 2.0), (41, 2.0),
    (48, 2.0), (48, 2.0),
    (43, 2.0), (43, 2.0),
]
MENU_LEAD = eighths([
    69, 72, 76, 72, 69, 72, 76, 79,
    69, 72, 77, 72, 69, 72, 77, 81,
    72, 76, 79, 76, 72, 76, 79, 72,
    67, 71, 74, 71, 67, 71, 74, REST,
])
MENU_PAD = [
    (57, 4.0), (53, 4.0), (60, 4.0), (55, 4.0),
]

PROLOGUE_BPM = 72.0
PROLOGUE_BASS = [
    (45, 4.0), (41, 4.0), (48, 4.0), (43, 4.0),
]
PROLOGUE_LEAD = [
    (69, 1.5), (REST, 0.5), (72, 1.0), (REST, 1.0),
    (68, 1.5), (REST, 0.5), (65, 1.0), (REST, 1.0),
    (72, 1.5), (REST, 0.5), (76, 1.0), (REST, 1.0),
    (74, 1.5), (REST, 0.5), (71, 1.0), (REST, 1.0),
]
PROLOGUE_PAD = [
    (45, 4.0), (41, 4.0), (48, 4.0), (43, 4.0),
]

GAME_BPM = 128.0
GAME_BASS = eighths([
    45, 45, 57, 45, 45, 52, 45, 45,
    41, 41, 53, 41, 41, 48, 41, 41,
    48, 48, 60, 48, 48, 55, 48, 48,
    43, 43, 55, 43, 43, 50, 43, REST,
])
GAME_LEAD = eighths([
    69, 72, 76, 72, 69, 72, 76, 79,
    65, 69, 72, 69, 65, 69, 72, 76,
    72, 76, 79, 76, 72, 76, 79, 84,
    67, 71, 74, 71, 67, 71, 74, 79,
    69, 72, 76, 72, 76, 79, 76, 72,
    65, 69, 72, 69, 72, 76, 72, 69,
    72, 76, 79, 76, 79, 83, 79, 76,
    67, 71, 74, 79, 74, 71, 67, REST,
])

TRACKS = {
    "menu": lambda spb: mix(
        render(MENU_BASS, spb, square, 0.55, 0.5, 3.2),
        render(MENU_LEAD, spb, square, 0.34, 0.25, 4.0),
        render(MENU_PAD, spb, triangle, 0.20),
    ),
    "prologue": lambda spb: mix(
        render(PROLOGUE_BASS, spb, triangle, 0.55),
        render(PROLOGUE_LEAD, spb, square, 0.30, 0.125, 3.0),
        render(PROLOGUE_PAD, spb, square, 0.16, 0.5, 1.1),
    ),
    "game": lambda spb: mix(
        render(GAME_BASS, spb, square, 0.50, 0.5, 3.0),
        render(GAME_LEAD, spb, square, 0.30, 0.25, 3.6),
    ),
}

TEMPOS = {"menu": MENU_BPM, "prologue": PROLOGUE_BPM, "game": GAME_BPM}


def build(name: str) -> list[float]:
    return fade_tail(normalize(TRACKS[name](60.0 / TEMPOS[name])))


def main() -> None:
    for name in TRACKS:
        samples = build(name)
        path = write_wav(name, samples)
        seconds = path.stat().st_size / (SAMPLE_RATE * 2)
        print(f"{path.relative_to(OUT_DIR.parent.parent)}  {seconds:.3f}s")


if __name__ == "__main__":
    main()
