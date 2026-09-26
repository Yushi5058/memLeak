import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main
from src.chamber import Chamber
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
        self.prologue = Prologue(["one", "", "two"])

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
                self.prologue,
            )

    def test_title_ignores_unrelated_keys(self):
        self.assertIs(
            main.handle_key(pygame.K_x, State.TITLE, self.session, self.prologue),
            State.TITLE,
        )

    def test_confirm_key_leaves_title_for_prologue(self):
        for key in main.CONFIRM_KEYS:
            self.assertIs(
                main.handle_key(key, State.TITLE, self.session, self.prologue),
                State.PROLOGUE,
            )

    def test_prologue_key_completes_reveal_before_advancing(self):
        self.assertFalse(self.prologue.finished)
        self.assertIs(
            main.handle_key(
                pygame.K_RETURN, State.PROLOGUE, self.session, self.prologue
            ),
            State.PROLOGUE,
        )
        self.assertTrue(self.prologue.finished)

    def test_prologue_confirm_advances_once_reveal_is_complete(self):
        self.prologue.skip()
        self.assertIs(
            main.handle_key(
                pygame.K_RETURN, State.PROLOGUE, self.session, self.prologue
            ),
            State.PLAY,
        )

    def test_play_movement_keys_drain_allocation(self):
        before = self.session.earth_alloc
        for key in main.MOVE_KEYS:
            self.assertIs(
                main.handle_key(key, State.PLAY, self.session, self.prologue),
                State.PLAY,
            )
        self.assertLess(self.session.earth_alloc, before)

    def test_jump_key_is_accepted_in_play(self):
        self.assertIs(
            main.handle_key(pygame.K_SPACE, State.PLAY, self.session, self.prologue),
            State.PLAY,
        )

    def test_escape_toggles_pause(self):
        self.assertIs(
            main.handle_key(pygame.K_ESCAPE, State.PLAY, self.session, self.prologue),
            State.PAUSED,
        )
        self.assertIs(
            main.handle_key(pygame.K_ESCAPE, State.PAUSED, self.session, self.prologue),
            State.PLAY,
        )

    def test_pause_ignores_movement_keys(self):
        before = self.session.earth_alloc
        main.handle_key(pygame.K_RIGHT, State.PAUSED, self.session, self.prologue)
        self.assertEqual(self.session.earth_alloc, before)

    def test_r_restart_clears_run_and_returns_to_play(self):
        self.session.step(0.2, NO_KEYS)
        self.session.game_over = True
        for state in (State.GAMEOVER, State.CLEARED):
            self.assertIs(
                main.handle_key(pygame.K_r, state, self.session, self.prologue),
                State.PLAY,
            )
            self.assertEqual(self.session.elapsed, 0.0)
            self.assertFalse(self.session.game_over)
            self.assertFalse(self.session.won)

    def test_r_is_ignored_while_playing(self):
        before = self.session.earth_alloc
        self.assertIs(
            main.handle_key(pygame.K_r, State.PLAY, self.session, self.prologue),
            State.PLAY,
        )
        self.assertEqual(self.session.earth_alloc, before)


if __name__ == "__main__":
    unittest.main()
