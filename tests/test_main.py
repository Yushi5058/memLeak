import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main
from src.chamber import Chamber
from src.chapters import Narration
from src.flow import Flow
from src.progression import Progress
from src.prologue import Prologue
from src.session import Session
from src.settings import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.states import State


class NoKeys:
    def __getitem__(self, key):
        return False


NO_KEYS = NoKeys()


class MainShellTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.font = main.load_font()
        self.canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        self.chamber = Chamber()
        self.session = Session(self.chamber)
        self.prologue = Prologue([["one"], ["two"]])
        self.narration = Narration(self.prologue)

    def test_boot_lands_on_the_main_menu(self):
        recorded = []
        original_render = main.render
        with tempfile.TemporaryDirectory() as tmp:
            main.Progress = lambda: Progress(Path(tmp) / "progress.json")
            main.render = lambda canvas, chamber, session, state, *rest: recorded.append(state)
            try:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                main.main()
            finally:
                main.render = original_render
                del main.Progress
        self.assertTrue(recorded)
        self.assertIs(recorded[0], State.MENU)

    def test_every_state_maps_to_a_real_music_track(self):
        from src.audio import MUSIC_NAMES

        for state in State:
            self.assertIn(main.MUSIC_FOR_STATE[state], MUSIC_NAMES, state)

    def test_play_states_use_the_game_track(self):
        for state in (State.PLAY, State.CLEARED, State.GAMEOVER):
            self.assertEqual(main.MUSIC_FOR_STATE[state], "game", state)

    def test_menus_use_the_menu_track_and_prologue_its_own(self):
        for state in (
            State.TITLE,
            State.MENU,
            State.LEVEL_SELECT,
            State.SETTINGS,
            State.ACHIEVEMENTS,
            State.PAUSED,
        ):
            self.assertEqual(main.MUSIC_FOR_STATE[state], "menu", state)
        self.assertEqual(main.MUSIC_FOR_STATE[State.PROLOGUE], "prologue")

    def test_vendored_font_is_used_when_present(self):
        self.assertTrue(main.FONT_PATH.is_file())
        self.assertEqual(self.font.get_height(), 8)

    def test_load_font_falls_back_when_font_missing(self):
        original = main.FONT_PATH
        main.FONT_PATH = original.parent / "does-not-exist.ttf"
        try:
            fallback = main.load_font()
        finally:
            main.FONT_PATH = original
        self.assertIsInstance(fallback, pygame.font.Font)

    def test_every_state_renders_without_crashing(self):
        for state in State:
            main.render(
                self.canvas,
                self.chamber,
                self.session,
                state,
                self.font,
                self.narration,
            )

    def test_title_ignores_unrelated_keys(self):
        self.assertIs(
            main.handle_key(pygame.K_x, State.TITLE, self.session, self.narration),
            State.TITLE,
        )

    def test_confirm_key_leaves_title_for_prologue(self):
        for key in main.CONFIRM_KEYS:
            self.assertIs(
                main.handle_key(key, State.TITLE, self.session, self.narration),
                State.PROLOGUE,
            )

    def test_prologue_key_completes_the_current_phase_first(self):
        self.assertFalse(self.prologue.phase_finished)
        self.assertIs(
            main.handle_key(pygame.K_RETURN, State.PROLOGUE, self.session, self.narration),
            State.PROLOGUE,
        )
        self.assertTrue(self.prologue.phase_finished)
        self.assertFalse(self.prologue.finished)

    def test_prologue_confirm_walks_every_phase_then_starts_play(self):
        state = State.PROLOGUE
        for _ in range(self.prologue.phase_count * 2):
            state = main.handle_key(pygame.K_RETURN, State.PROLOGUE, self.session, self.narration)
        self.assertIs(state, State.PLAY)
        self.assertTrue(self.prologue.finished)

    def test_completing_the_prologue_persists_that_it_was_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            progress = Progress(path)
            flow = Flow(progress)
            state = State.PROLOGUE
            for _ in range(self.prologue.phase_count * 2):
                state = main.handle_key(
                    pygame.K_RETURN,
                    State.PROLOGUE,
                    self.session,
                    self.narration,
                    flow,
                )
            self.assertIs(state, State.PLAY)
            self.assertTrue(progress.seen_prologue)
            self.assertTrue(path.is_file())
            self.assertTrue(Progress(path).seen_prologue)

    def test_s_skips_the_whole_script_straight_into_play(self):
        self.assertIs(
            main.handle_key(pygame.K_s, State.PROLOGUE, self.session, self.narration),
            State.PLAY,
        )
        self.assertTrue(self.prologue.finished)

    def test_s_is_ignored_while_playing(self):
        before = self.session.earth_alloc
        self.assertIs(
            main.handle_key(pygame.K_s, State.PLAY, self.session, self.narration),
            State.PLAY,
        )
        self.assertEqual(self.session.earth_alloc, before)

    def test_skipping_the_prologue_still_records_it_as_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            flow = Flow(Progress(path))
            self.assertIs(
                main.handle_key(pygame.K_s, State.PROLOGUE, self.session, self.narration, flow),
                State.PLAY,
            )
            self.assertTrue(Progress(path).seen_prologue)

    def test_enter_on_a_cleared_chamber_with_a_next_one_advances(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = Flow(Progress(Path(tmp) / "progress.json"))
            flow.start(0)
            self.assertFalse(flow.all_cleared)
            self.assertIs(
                main.handle_key(
                    pygame.K_RETURN,
                    State.CLEARED,
                    flow.session,
                    self.narration,
                    flow,
                ),
                State.PROLOGUE,
            )
            self.assertEqual(flow.level_index, 1)

    def test_enter_on_the_final_cleared_chamber_returns_to_the_main_menu(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = Flow(Progress(Path(tmp) / "progress.json"))
            flow.start(flow.level_count - 1)
            for index in range(flow.level_count):
                flow.progress.record_clear(index, 10.0, 300.0)
            self.assertTrue(flow.all_cleared)
            self.assertFalse(flow.advance())
            self.assertIs(
                main.handle_key(
                    pygame.K_RETURN,
                    State.CLEARED,
                    flow.session,
                    self.narration,
                    flow,
                ),
                State.MENU,
            )

    def test_play_movement_keys_drain_allocation(self):
        before = self.session.earth_alloc
        for key in main.MOVE_KEYS:
            self.assertIs(
                main.handle_key(key, State.PLAY, self.session, self.narration),
                State.PLAY,
            )
        self.assertLess(self.session.earth_alloc, before)

    def test_jump_key_is_accepted_in_play(self):
        self.assertIs(
            main.handle_key(pygame.K_SPACE, State.PLAY, self.session, self.narration),
            State.PLAY,
        )

    def test_escape_toggles_pause(self):
        self.assertIs(
            main.handle_key(pygame.K_ESCAPE, State.PLAY, self.session, self.narration),
            State.PAUSED,
        )
        self.assertIs(
            main.handle_key(pygame.K_ESCAPE, State.PAUSED, self.session, self.narration),
            State.PLAY,
        )

    def test_pause_ignores_movement_keys(self):
        before = self.session.earth_alloc
        main.handle_key(pygame.K_RIGHT, State.PAUSED, self.session, self.narration)
        self.assertEqual(self.session.earth_alloc, before)

    def test_r_restart_clears_run_and_returns_to_play(self):
        self.session.step(0.2, NO_KEYS)
        self.session.game_over = True
        for state in (State.GAMEOVER, State.CLEARED):
            self.assertIs(
                main.handle_key(pygame.K_r, state, self.session, self.narration),
                State.PLAY,
            )
            self.assertEqual(self.session.elapsed, 0.0)
            self.assertFalse(self.session.game_over)
            self.assertFalse(self.session.won)

    def test_r_is_ignored_while_playing(self):
        before = self.session.earth_alloc
        self.assertIs(
            main.handle_key(pygame.K_r, State.PLAY, self.session, self.narration),
            State.PLAY,
        )
        self.assertEqual(self.session.earth_alloc, before)


if __name__ == "__main__":
    unittest.main()
