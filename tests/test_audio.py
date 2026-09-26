import importlib.util
import os
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.audio import (
    DEFAULT_MUSIC_DIR,
    DEFAULT_SOUNDS_DIR,
    MUSIC_NAMES,
    SOUND_NAMES,
    VOLUME_STEPS,
    Audio,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_sfx", REPO_ROOT / "tools" / "gen_sfx.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_music_generator():
    spec = importlib.util.spec_from_file_location("gen_music", REPO_ROOT / "tools" / "gen_music.py")
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
            self.assertFalse(any(v <= -32768 or v >= 32767 for v in samples), f"{name} wrapped")

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


class MusicTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.audio = Audio()

    def test_all_music_files_exist(self):
        for name in MUSIC_NAMES:
            self.assertTrue((DEFAULT_MUSIC_DIR / f"{name}.wav").is_file(), name)

    def test_music_files_are_mono_16bit_at_the_mixer_rate(self):
        for name in MUSIC_NAMES:
            with wave.open(str(DEFAULT_MUSIC_DIR / f"{name}.wav")) as wav:
                self.assertEqual(wav.getnchannels(), 1, name)
                self.assertEqual(wav.getsampwidth(), 2, name)
                self.assertEqual(wav.getframerate(), 22050, name)

    def test_music_tracks_are_long_enough_to_loop(self):
        for name in MUSIC_NAMES:
            with wave.open(str(DEFAULT_MUSIC_DIR / f"{name}.wav")) as wav:
                seconds = wav.getnframes() / wav.getframerate()
            self.assertGreater(seconds, 4.0, name)

    def test_music_is_audible_and_not_clipped(self):
        for name in MUSIC_NAMES:
            with wave.open(str(DEFAULT_MUSIC_DIR / f"{name}.wav")) as wav:
                samples = array("h", wav.readframes(wav.getnframes()))
            peak = max(max(samples), -min(samples))
            self.assertGreater(peak, 8000, f"{name} is effectively silent")
            self.assertLess(peak, 32767, f"{name} is clipping")
            self.assertFalse(any(v <= -32768 or v >= 32767 for v in samples), f"{name} wrapped")

    def test_music_loops_start_and_end_at_silence(self):
        for name in MUSIC_NAMES:
            with wave.open(str(DEFAULT_MUSIC_DIR / f"{name}.wav")) as wav:
                samples = array("h", wav.readframes(wav.getnframes()))
            self.assertLessEqual(abs(samples[0]), 4, f"{name} starts out of silence")
            self.assertLessEqual(abs(samples[-1]), 4, f"{name} ends out of silence")
            tail = max(abs(v) for v in samples[-256:])
            self.assertLess(tail, 2000, f"{name} rings into the loop point")

    def test_committed_music_matches_a_fresh_synthesis(self):
        gen = load_music_generator()
        original = gen.OUT_DIR
        with tempfile.TemporaryDirectory() as tmp:
            gen.OUT_DIR = Path(tmp)
            try:
                for name in MUSIC_NAMES:
                    fresh = gen.write_wav(name, gen.build(name))
                    committed = (DEFAULT_MUSIC_DIR / f"{name}.wav").read_bytes()
                    self.assertEqual(fresh.read_bytes(), committed, f"{name} is stale")
            finally:
                gen.OUT_DIR = original

    def test_generator_is_deterministic(self):
        gen = load_music_generator()
        for name in MUSIC_NAMES:
            self.assertEqual(gen.build(name), gen.build(name), name)

    def test_play_music_never_raises_for_known_or_unknown_tracks(self):
        for name in (*MUSIC_NAMES, "does-not-exist", "", "MENU"):
            self.audio.play_music(name)

    def test_playing_a_track_records_it_as_current(self):
        self.audio.play_music("menu")
        self.assertEqual(self.audio.current_music, "menu")

    def test_switching_tracks_replaces_the_current_one(self):
        self.audio.play_music("menu")
        self.audio.play_music("game")
        self.assertEqual(self.audio.current_music, "game")

    def test_replaying_the_same_track_does_not_restart_it(self):
        self.audio.play_music("menu")
        self.audio.play_music("menu")
        self.assertEqual(self.audio.current_music, "menu")

    def test_stop_music_clears_the_current_track(self):
        self.audio.play_music("menu")
        self.audio.stop_music()
        self.assertIsNone(self.audio.current_music)

    def test_missing_music_dir_is_safe(self):
        audio = Audio(music_dir=Path("/nonexistent/music"))
        for name in MUSIC_NAMES:
            audio.play_music(name)
        self.assertIsNone(audio.current_music)
        audio.stop_music()

    def test_music_volume_clamps_to_the_step_range(self):
        for _ in range(VOLUME_STEPS + 3):
            self.audio.adjust_music(1)
        self.assertEqual(self.audio.music_volume, VOLUME_STEPS)
        for _ in range(VOLUME_STEPS * 2):
            self.audio.adjust_music(-1)
        self.assertEqual(self.audio.music_volume, 0)

    def test_music_label_tracks_the_volume(self):
        self.assertEqual(self.audio.music_label, f"{VOLUME_STEPS}/{VOLUME_STEPS}")
        self.audio.adjust_music(-1)
        self.assertEqual(self.audio.music_label, f"{VOLUME_STEPS - 1}/{VOLUME_STEPS}")

    def test_mute_silences_both_music_and_sound_labels(self):
        self.audio.toggle_mute()
        self.assertEqual(self.audio.music_label, "OFF")
        self.assertEqual(self.audio.sfx_label, "OFF")
        self.assertTrue(self.audio.muted)

    def test_music_stays_silent_but_tracked_while_muted(self):
        self.audio.play_music("game")
        self.audio.toggle_mute()
        self.assertEqual(self.audio.current_music, "game")
        self.assertEqual(self.audio.music_label, "OFF")


if __name__ == "__main__":
    unittest.main()
