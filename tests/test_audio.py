import importlib.util
import os
import unittest
import wave
from array import array
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.audio import DEFAULT_SOUNDS_DIR, SOUND_NAMES, Audio

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_sfx", REPO_ROOT / "tools" / "gen_sfx.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AudioTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.audio = Audio()

    def test_all_sound_files_exist(self):
        for name in SOUND_NAMES:
            self.assertTrue((DEFAULT_SOUNDS_DIR / f"{name}.wav").is_file(), name)

    def test_sound_files_are_short_mono_16bit(self):
        for name in SOUND_NAMES:
            with wave.open(str(DEFAULT_SOUNDS_DIR / f"{name}.wav")) as wav:
                self.assertEqual(wav.getnchannels(), 1, name)
                self.assertEqual(wav.getsampwidth(), 2, name)
                self.assertEqual(wav.getframerate(), 22050, name)
                self.assertLess(wav.getnframes() / wav.getframerate(), 1.0, name)

    def test_sound_files_are_audible_and_not_clipped(self):
        for name in SOUND_NAMES:
            with wave.open(str(DEFAULT_SOUNDS_DIR / f"{name}.wav")) as wav:
                samples = array("h", wav.readframes(wav.getnframes()))
            peak = max(max(samples), -min(samples))
            self.assertGreater(peak, 2000, f"{name} is effectively silent")
            self.assertLess(peak, 32767, f"{name} is clipping")
            self.assertFalse(
                any(v <= -32768 or v >= 32767 for v in samples), f"{name} wrapped"
            )

    def test_committed_files_match_a_fresh_synthesis(self):
        gen = load_generator()
        for name in SOUND_NAMES:
            fresh = gen.SOUNDS[name]()
            with wave.open(str(DEFAULT_SOUNDS_DIR / f"{name}.wav")) as wav:
                committed = array("h", wav.readframes(wav.getnframes()))
            self.assertEqual(list(fresh), list(committed), f"{name} is stale")

    def test_play_never_raises_for_known_or_unknown_names(self):
        for name in (*SOUND_NAMES, "does-not-exist", "", "JUMP"):
            self.audio.play(name)

    def test_missing_sound_dir_disables_audio_without_raising(self):
        audio = Audio(sounds_dir=Path("/nonexistent/sounds"))
        self.assertFalse(audio.available)
        for name in SOUND_NAMES:
            audio.play(name)

    def test_available_reflects_loaded_sounds(self):
        self.assertEqual(self.audio.available, bool(self.audio._sounds))


if __name__ == "__main__":
    unittest.main()
