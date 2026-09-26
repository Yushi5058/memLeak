import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import src.screens as screens_module
from main import FONT_PATH, FONT_SIZE, SMALL_FONT_PATH, SMALL_FONT_SIZE
from src.achievements import ACHIEVEMENTS, Achievement
from src.audio import VOLUME_STEPS, Audio
from src.flow import Flow
from src.levels import LEVELS
from src.progression import Progress
from src.screens import Screens
from src.settings import BG_COLOR, EARNED_TILE_COLOR, LOCKED_TILE_COLOR
from src.states import State


def ink_size(font, text):
    """Width and tallest-ink-row height of `text`, ignoring side bearing."""
    image = font.render(text, False, (255, 255, 255), (0, 0, 0))
    width, height = image.get_size()
    rows = [
        y
        for y in range(height)
        if any(image.get_at((x, y))[0] > 127 for x in range(width))
    ]
    return width, (rows[-1] - rows[0] + 1) if rows else 0


class SurfaceSpy:
    """Delegates to a real surface while recording blits and fills."""

    def __init__(self, real):
        self.real = real
        self.blits = []
        self.fills = []

    def get_width(self):
        return self.real.get_width()

    def get_height(self):
        return self.real.get_height()

    def blit(self, surface, pos, *args, **kwargs):
        self.blits.append((surface.get_width(), pos[0]))
        return self.real.blit(surface, pos, *args, **kwargs)

    def fill(self, color, rect=None, *args, **kwargs):
        self.fills.append((color, rect))
        return self.real.fill(color, rect, *args, **kwargs)


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
        self.pixel_font = pygame.font.Font(str(FONT_PATH), FONT_SIZE)
        self.small_font = pygame.font.Font(str(SMALL_FONT_PATH), SMALL_FONT_SIZE)
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

    def test_achievement_rows_are_centered(self):
        spy = SurfaceSpy(self.canvas)
        self.screens.draw(spy, self.pixel_font, State.ACHIEVEMENTS, self.small_font)
        self.assertTrue(spy.blits)
        width = self.canvas.get_width()
        tiles = [rect for _, rect in spy.fills if rect is not None]
        self.assertTrue(tiles)
        for tile in tiles:
            self.assertEqual(tile[0], (width - tile[2]) // 2)
        for surface_width, x in spy.blits:
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x + surface_width, width)

    def test_achievement_text_fits_inside_the_screen(self):
        for achievement in ACHIEVEMENTS:
            for text in (f"* {achievement.label}", achievement.hint):
                self.assertLessEqual(
                    self.pixel_font.size(text)[0], self.canvas.get_width()
                )
                self.assertLessEqual(
                    self.small_font.size(text)[0], self.canvas.get_width()
                )

    def test_rows_are_backed_by_a_tile_that_differentiates_earned_from_locked(self):
        self.progress.unlock_achievement(ACHIEVEMENTS[0].key)
        spy = SurfaceSpy(self.canvas)
        self.screens.draw(spy, self.pixel_font, State.ACHIEVEMENTS, self.small_font)
        painted = {color for color, rect in spy.fills if rect is not None}
        self.assertIn(EARNED_TILE_COLOR, painted)
        self.assertIn(LOCKED_TILE_COLOR, painted)

    def test_every_row_gets_a_tile(self):
        spy = SurfaceSpy(self.canvas)
        self.screens.draw(spy, self.pixel_font, State.ACHIEVEMENTS, self.small_font)
        tiles = [rect for _, rect in spy.fills if rect is not None]
        self.assertEqual(len(tiles), len(ACHIEVEMENTS))
        for rect in tiles:
            self.assertGreaterEqual(rect[0], 0)
            self.assertLessEqual(rect[0] + rect[2], self.canvas.get_width())
            self.assertLessEqual(rect[1] + rect[3], self.canvas.get_height())

    def test_the_description_font_is_smaller_than_the_label_font(self):
        """Micro 5 is a small pixel face: much narrower per glyph, never taller."""
        achievement = ACHIEVEMENTS[0]
        label = f"* {achievement.label}"
        hint = achievement.hint
        _, label_h = ink_size(self.pixel_font, label)
        hint_w, hint_h = ink_size(self.small_font, hint)
        self.assertLessEqual(hint_h, label_h)
        big_per_char = self.pixel_font.size(hint)[0] / len(hint)
        small_per_char = self.small_font.size(hint)[0] / len(hint)
        self.assertLess(small_per_char, big_per_char * 0.75)
        self.assertLess(hint_w, self.pixel_font.size(hint)[0])

    def test_a_locked_row_still_shows_its_name_and_its_goal(self):
        self.progress.achievements = []
        spy = SurfaceSpy(self.canvas)
        self.screens.draw(spy, self.pixel_font, State.ACHIEVEMENTS, self.small_font)
        self.assertTrue(spy.blits)
        self.assertEqual(len(spy.blits), len(ACHIEVEMENTS) * 2 + 2)

    def test_everything_still_fits_once_secrets_are_added(self):
        extra = (
            Achievement("secret_one", "SECRET ONE", "A deliberately long goal line"),
            Achievement("secret_two", "SECRET TWO", "Another long goal line here"),
        )
        original = screens_module.ACHIEVEMENTS
        screens_module.ACHIEVEMENTS = ACHIEVEMENTS + extra
        try:
            spy = SurfaceSpy(self.canvas)
            self.screens.draw(spy, self.pixel_font, State.ACHIEVEMENTS, self.small_font)
        finally:
            screens_module.ACHIEVEMENTS = original
        for surface_width, x in spy.blits:
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x + surface_width, self.canvas.get_width())
        for _, rect in spy.fills:
            if rect is not None:
                self.assertLessEqual(rect[1] + rect[3], self.canvas.get_height())


if __name__ == "__main__":
    unittest.main()
