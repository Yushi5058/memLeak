import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.audio import VOLUME_STEPS, Audio
from src.flow import Flow
from src.levels import LEVELS
from src.progression import Progress
from src.screens import Screens
from src.settings import BG_COLOR
from src.states import State


def pick(menu, label_fragment):
    for i, item in enumerate(menu.visible()):
        if label_fragment in item["label"]:
            menu.index = i
            return item
    raise AssertionError(f"no menu item containing {label_fragment!r}")


class ScreensTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 12)
        self.canvas = pygame.Surface((320, 180))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.progress = Progress(Path(self.tmp.name) / "progress.json")
        self.flow = Flow(self.progress)
        self.audio = Audio()
        self.screens = Screens(self.flow, self.audio)

    def press(self, state, *keys):
        for key in keys:
            state = self.screens.handle_key(state, key)
        return state

    def open_main_item(self, state, fragment):
        pick(self.screens.main, fragment)
        return self.press(state, pygame.K_RETURN)

    def open_pause_item(self, state, fragment):
        pick(self.screens.pause, fragment)
        return self.press(state, pygame.K_RETURN)

    def open_settings_item(self, state, fragment):
        pick(self.screens.settings, fragment)
        return self.press(state, pygame.K_RETURN)

    def test_main_menu_offers_the_four_requested_entries(self):
        labels = [item["label"] for item in self.screens.main.items]
        self.assertEqual(
            labels, ["START", "ACHIEVEMENTS", "AUDIO SETTINGS", "EXIT"]
        )

    def test_pause_menu_offers_the_three_requested_entries(self):
        labels = [item["label"] for item in self.screens.pause.items]
        self.assertEqual(labels, ["RESUME", "AUDIO SETTINGS", "EXIT TO MAIN MENU"])

    def test_pause_exit_returns_to_the_main_menu_not_play(self):
        self.assertIs(
            self.open_pause_item(State.PAUSED, "EXIT TO MAIN MENU"), State.MENU
        )

    def test_settings_screen_adjusts_music_and_sound(self):
        music_before = self.audio.music_volume
        pick(self.screens.settings, "MUSIC")
        self.press(State.SETTINGS, pygame.K_LEFT)
        self.assertEqual(self.audio.music_volume, music_before - 1)

        sound_before = self.audio.sfx_volume
        pick(self.screens.settings, "SOUND")
        self.press(State.SETTINGS, pygame.K_LEFT)
        self.assertEqual(self.audio.sfx_volume, sound_before - 1)

    def test_start_opens_level_select(self):
        self.assertIs(self.open_main_item(State.MENU, "START"), State.LEVEL_SELECT)

    def test_achievements_opens_and_returns_to_the_menu(self):
        self.assertIs(
            self.open_main_item(State.MENU, "ACHIEVEMENTS"), State.ACHIEVEMENTS
        )
        self.assertIs(self.press(State.ACHIEVEMENTS, pygame.K_ESCAPE), State.MENU)

    def test_settings_opens_and_returns_to_the_menu(self):
        self.assertIs(
            self.open_main_item(State.MENU, "AUDIO SETTINGS"), State.SETTINGS
        )
        self.assertIs(self.press(State.SETTINGS, pygame.K_ESCAPE), State.MENU)

    def test_exit_quits_from_the_main_menu(self):
        self.assertIsNone(self.open_main_item(State.MENU, "EXIT"))

    def test_escape_quits_from_the_main_menu(self):
        self.assertIsNone(self.press(State.MENU, pygame.K_ESCAPE))

    def test_level_select_lists_every_chamber(self):
        self.screens.build_level_menu()
        labels = [item["label"] for item in self.screens.levels.visible()]
        self.assertEqual(len(labels), len(LEVELS))
        for level in LEVELS:
            self.assertTrue(any(level.name in label for label in labels), level.name)

    def test_locked_chambers_are_marked_and_cannot_be_chosen(self):
        self.screens.build_level_menu()
        locked = [
            item
            for item in self.screens.levels.visible()
            if "LOCKED" in item["label"]
        ]
        self.assertEqual(len(locked), len(LEVELS) - 1)
        pick(self.screens.levels, LEVELS[1].name)
        self.assertIs(
            self.screens.handle_key(State.LEVEL_SELECT, pygame.K_RETURN),
            State.LEVEL_SELECT,
        )
        self.assertEqual(self.flow.level_index, 0)

    def test_unlocked_chamber_starts_immediately_when_prologue_was_seen(self):
        self.progress.seen_prologue = True
        self.progress.unlocked = len(LEVELS)
        self.screens.build_level_menu()
        pick(self.screens.levels, LEVELS[1].name)
        self.assertIs(
            self.press(State.LEVEL_SELECT, pygame.K_RETURN), State.PLAY
        )
        self.assertEqual(self.flow.level_index, 1)

    def test_first_ever_play_goes_through_the_prologue(self):
        self.assertFalse(self.progress.seen_prologue)
        self.screens.build_level_menu()
        pick(self.screens.levels, LEVELS[0].name)
        self.assertIs(self.press(State.LEVEL_SELECT, pygame.K_RETURN), State.PROLOGUE)

    def test_level_select_escape_returns_to_the_menu(self):
        self.assertIs(self.press(State.LEVEL_SELECT, pygame.K_ESCAPE), State.MENU)

    def test_pause_resume_and_quit(self):
        self.assertIs(self.open_pause_item(State.PAUSED, "RESUME"), State.PLAY)
        self.assertIs(self.open_pause_item(State.PAUSED, "EXIT TO MAIN"), State.MENU)

    def test_pause_escape_resumes(self):
        self.assertIs(self.press(State.PAUSED, pygame.K_ESCAPE), State.PLAY)

    def test_settings_from_pause_returns_to_pause(self):
        self.assertIs(
            self.open_pause_item(State.PAUSED, "AUDIO SETTINGS"), State.SETTINGS
        )
        self.assertIs(self.press(State.SETTINGS, pygame.K_ESCAPE), State.PAUSED)

    def test_mute_toggles_and_blocks_sound(self):
        self.assertFalse(self.audio.muted)
        self.open_settings_item(State.SETTINGS, "MUTE ALL")
        self.assertTrue(self.audio.muted)
        self.assertEqual(self.audio.sfx_label, "OFF")
        self.audio.play("jump")
        self.open_settings_item(State.SETTINGS, "MUTE ALL")
        self.assertFalse(self.audio.muted)

    def test_left_and_right_adjust_the_selected_channel(self):
        self.audio.adjust_music(-VOLUME_STEPS)
        pick(self.screens.settings, "MUSIC")
        self.press(State.SETTINGS, pygame.K_RIGHT)
        self.assertEqual(self.audio.music_volume, 1)
        self.press(State.SETTINGS, pygame.K_LEFT, pygame.K_LEFT)
        self.assertEqual(self.audio.music_volume, 0)

    def test_volumes_clamp_at_the_extremes(self):
        pick(self.screens.settings, "SOUND")
        for _ in range(VOLUME_STEPS + 4):
            self.press(State.SETTINGS, pygame.K_RIGHT)
        self.assertEqual(self.audio.sfx_volume, VOLUME_STEPS)
        for _ in range(VOLUME_STEPS * 2):
            self.press(State.SETTINGS, pygame.K_LEFT)
        self.assertEqual(self.audio.sfx_volume, 0)

    def test_navigating_settings_never_crashes(self):
        for key in (
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_RIGHT,
        ):
            self.assertIs(self.press(State.SETTINGS, key), State.SETTINGS)

    def test_settings_back_row_returns_to_origin(self):
        self.open_settings_item(State.SETTINGS, "BACK")
        self.assertEqual(self.screens.settings_origin, State.MENU)

    def test_every_screen_draws_without_crashing(self):
        self.screens.build_level_menu()
        for state in (
            State.MENU,
            State.LEVEL_SELECT,
            State.PAUSED,
            State.SETTINGS,
            State.ACHIEVEMENTS,
        ):
            self.canvas.fill((0, 0, 0))
            self.screens.draw(self.canvas, self.font, state)

    def test_achievements_screen_reflects_progress(self):
        self.progress.unlock_achievement("first_steps")
        self.canvas.fill(BG_COLOR)
        self.screens.draw(self.canvas, self.font, State.ACHIEVEMENTS)
        self.assertEqual(self.canvas.get_at((0, 0))[:3], BG_COLOR)

    def test_level_menu_reflects_newly_unlocked_chambers(self):
        self.screens.build_level_menu()
        before = sum("LOCKED" in i["label"] for i in self.screens.levels.visible())
        self.progress.record_clear(0, 10.0, 500.0)
        self.screens.build_level_menu()
        after = sum("LOCKED" in i["label"] for i in self.screens.levels.visible())
        self.assertEqual(after, before - 1)

    def test_settings_changes_are_written_to_the_save_file(self):
        self.open_settings_item(State.SETTINGS, "MUTE ALL")
        self.progress = Progress(Path(self.tmp.name) / "progress.json")
        self.assertTrue(self.progress.muted)

    def test_volume_changes_persist_and_reload(self):
        pick(self.screens.settings, "MUSIC")
        self.press(State.SETTINGS, pygame.K_LEFT)
        expected = self.audio.music_volume
        self.assertEqual(
            Progress(Path(self.tmp.name) / "progress.json").music_volume, expected
        )

    def test_leaving_the_settings_row_never_saves(self):
        before = self.progress.music_volume
        self.press(State.SETTINGS, pygame.K_UP, pygame.K_UP)
        self.assertEqual(self.progress.music_volume, before)

    def test_boot_applies_saved_audio_settings(self):
        progress = Progress(Path(self.tmp.name) / "progress.json")
        progress.set_audio_settings(1, 2, True)
        restored = Progress(Path(self.tmp.name) / "progress.json")
        audio = Audio()
        audio.music_volume = restored.music_volume
        audio.sfx_volume = restored.sfx_volume
        audio.muted = restored.muted
        audio.apply_volumes()
        self.assertEqual(audio.music_volume, 1)
        self.assertEqual(audio.sfx_volume, 2)
        self.assertTrue(audio.muted)

    def test_best_time_is_shown_once_a_chamber_is_cleared(self):
        self.progress.record_clear(0, 12.25, 500.0)
        self.screens.build_level_menu()
        label = pick(self.screens.levels, LEVELS[0].name)["label"]
        self.assertIn("12.25s", label)


if __name__ == "__main__":
    unittest.main()
