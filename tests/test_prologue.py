import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.prologue import MAX_COLUMNS, PROLOGUE_PATH, PROMPT, Prologue
from src.settings import INTERNAL_HEIGHT, INTERNAL_WIDTH


class PrologueTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 8)
        self.prologue = Prologue.from_file()

    def test_shipped_script_loads(self):
        self.assertTrue(PROLOGUE_PATH.is_file())
        self.assertTrue(self.prologue.lines)

    def test_no_line_exceeds_the_terminal_width(self):
        for line in self.prologue.lines:
            self.assertLessEqual(len(line), MAX_COLUMNS, line)

    def test_whole_script_fits_on_one_screen(self):
        leading = self.font.get_linesize()
        self.assertLessEqual(len(self.prologue.lines) * leading, INTERNAL_HEIGHT)

    def test_reveal_starts_empty(self):
        self.assertEqual(self.prologue.visible_lines(), [])
        self.assertFalse(self.prologue.finished)

    def test_update_reveals_progressively(self):
        self.prologue.update(0.5)
        self.assertTrue(self.prologue.visible_lines())
        self.assertFalse(self.prologue.finished)

    def test_visible_lines_only_grow(self):
        previous = 0
        for _ in range(1200):
            self.prologue.update(1 / 60)
            count = len(self.prologue.visible_lines())
            self.assertGreaterEqual(count, previous)
            previous = count
        self.assertTrue(self.prologue.finished)

    def test_reveal_never_exceeds_the_script(self):
        for _ in range(1000):
            self.prologue.update(1.0)
        self.assertEqual(self.prologue.visible_lines(), self.prologue.lines)

    def test_skip_reveals_everything_immediately(self):
        self.prologue.skip()
        self.assertTrue(self.prologue.finished)
        self.assertEqual(self.prologue.visible_lines(), self.prologue.lines)

    def test_update_after_finishing_is_a_noop(self):
        self.prologue.skip()
        self.prologue.update(5.0)
        self.assertEqual(self.prologue.visible_lines(), self.prologue.lines)

    def test_blank_lines_are_preserved_as_spacers(self):
        self.assertIn("", self.prologue.lines)
        self.prologue.skip()
        self.assertIn("", self.prologue.visible_lines())

    def test_partial_line_is_truncated_mid_word(self):
        prologue = Prologue(["abcdefghij"])
        prologue.revealed = 4.0
        self.assertEqual(prologue.visible_lines(), ["abcd"])

    def test_empty_script_is_immediately_finished(self):
        self.assertTrue(Prologue([]).finished)

    def test_draw_does_not_crash_at_any_stage(self):
        surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        for _ in range(60):
            self.prologue.update(1 / 60)
            self.prologue.draw(surface, self.font)
        self.prologue.skip()
        self.prologue.draw(surface, self.font)

    def test_prompt_does_not_collide_with_the_first_line(self):
        first_line_width = self.font.size(self.prologue.lines[0])[0]
        prompt_width = self.font.size(PROMPT)[0]
        prompt_x = INTERNAL_WIDTH - prompt_width - 4
        self.assertGreaterEqual(prompt_x, first_line_width)


if __name__ == "__main__":
    unittest.main()
