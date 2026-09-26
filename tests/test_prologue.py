import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.prologue import (
    BLINK_INTERVAL_MS,
    CHARS_PER_SECOND,
    MARGIN,
    MAX_COLUMNS,
    PROLOGUE_PATH,
    PROMPT,
    PROMPT_GAP,
    PROMPT_MARGIN,
    SKIP_PROMPT,
    TEXT_SCALE,
    Prologue,
    parse_phases,
)
from src.settings import BG_COLOR, INTERNAL_HEIGHT, INTERNAL_WIDTH


class PrologueTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 8)
        self.surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        self.prologue = Prologue.from_file()

    def drawn_columns(self, surface, y_stop=None):
        if y_stop is None:
            y_stop = surface.get_height()
        return [
            x
            for x in range(surface.get_width())
            if any(surface.get_at((x, y))[:3] != BG_COLOR for y in range(y_stop))
        ]

    def prompt_band_runs(self, script):
        self.surface.fill(BG_COLOR)
        script.draw(self.surface, self.font)
        band = range(INTERNAL_HEIGHT - 20, INTERNAL_HEIGHT)
        columns = [
            x
            for x in range(INTERNAL_WIDTH)
            if any(self.surface.get_at((x, y))[:3] != BG_COLOR for y in band)
        ]
        if not columns:
            return []
        runs, start, previous = [], columns[0], columns[0]
        for column in columns[1:]:
            if column != previous + 1:
                runs.append((start, previous))
                start = column
            previous = column
        runs.append((start, previous))
        return runs

    def skip_x(self):
        width = self.font.size(SKIP_PROMPT)[0] * TEXT_SCALE
        return INTERNAL_WIDTH - width - PROMPT_MARGIN

    def test_shipped_script_loads(self):
        self.assertTrue(PROLOGUE_PATH.is_file())
        self.assertTrue(self.prologue.phases)

    def test_script_is_split_into_six_phases(self):
        self.assertEqual(self.prologue.phase_count, 6)

    def test_final_beat_is_gated_behind_its_own_enter(self):
        phases = self.prologue.phases
        self.assertEqual(phases[-1], ["Nothing else", "matters."])
        self.assertEqual(phases[-2][-1], "Reach the gate.")

        while self.prologue.phase_index < len(phases) - 2:
            self.prologue.advance()
            self.prologue.advance()
        self.assertEqual(self.prologue.lines[-1], "Reach the gate.")
        self.assertNotIn("Nothing else", self.prologue.lines)

        self.prologue.advance()
        self.prologue.advance()
        self.assertEqual(self.prologue.phase_index, len(phases) - 1)
        self.assertEqual(self.prologue.lines, ["Nothing else", "matters."])

    def test_no_line_exceeds_eighteen_columns(self):
        self.assertEqual(MAX_COLUMNS, 18)
        for phase in self.prologue.phases:
            for line in phase:
                self.assertLessEqual(len(line), MAX_COLUMNS, line)

    def test_every_phase_fits_on_one_screen_when_doubled(self):
        leading = self.font.get_linesize() * TEXT_SCALE
        for phase in self.prologue.phases:
            self.assertLessEqual(len(phase) * leading, INTERNAL_HEIGHT, phase)

    def test_phases_are_wrapped_at_the_margin_width(self):
        widest = max(len(line) for phase in self.prologue.phases for line in phase)
        self.assertEqual(widest, MAX_COLUMNS)

    def test_widest_line_fits_between_the_side_margins(self):
        widest = self.font.size("M" * MAX_COLUMNS)[0] * TEXT_SCALE
        self.assertLessEqual(widest + 2 * MARGIN, INTERNAL_WIDTH)

    def test_reading_pace_is_human_rather_than_mashing(self):
        self.assertEqual(CHARS_PER_SECOND, 22.0)
        chars = sum(len(line) for phase in self.prologue.phases for line in phase)
        seconds = chars / CHARS_PER_SECOND
        self.assertGreater(seconds, 8.0)
        self.assertLess(seconds, 30.0)

    def test_reveal_starts_empty(self):
        self.assertEqual(self.prologue.visible_lines(), [])
        self.assertFalse(self.prologue.finished)

    def test_update_reveals_progressively(self):
        self.prologue.update(0.5)
        self.assertTrue(self.prologue.visible_lines())
        self.assertFalse(self.prologue.phase_finished)

    def test_visible_lines_only_grow_within_a_phase(self):
        previous = 0
        for _ in range(600):
            self.prologue.update(1 / 60)
            count = len(self.prologue.visible_lines())
            self.assertGreaterEqual(count, previous)
            previous = count
        self.assertTrue(self.prologue.phase_finished)

    def test_update_never_leaks_into_the_next_phase(self):
        self.prologue.update(60.0)
        self.assertEqual(self.prologue.phase_index, 0)
        self.assertEqual(self.prologue.visible_lines(), self.prologue.phases[0])

    def test_skip_reveals_the_current_phase_only(self):
        self.prologue.skip()
        self.assertTrue(self.prologue.phase_finished)
        self.assertFalse(self.prologue.finished)
        self.assertEqual(self.prologue.visible_lines(), self.prologue.phases[0])

    def test_first_advance_completes_the_phase_without_leaving_it(self):
        self.assertTrue(self.prologue.advance())
        self.assertEqual(self.prologue.phase_index, 0)
        self.assertTrue(self.prologue.phase_finished)

    def test_second_advance_moves_to_the_next_phase(self):
        self.prologue.advance()
        self.assertTrue(self.prologue.advance())
        self.assertEqual(self.prologue.phase_index, 1)
        self.assertEqual(self.prologue.revealed, 0.0)
        self.assertEqual(self.prologue.visible_lines(), [])

    def test_advance_reports_the_end_only_after_the_last_phase(self):
        presses = 0
        while self.prologue.advance():
            presses += 1
            self.assertLess(presses, 50, "advance never reported the end")
        self.assertEqual(presses, self.prologue.phase_count * 2 - 1)
        self.assertTrue(self.prologue.finished)

    def test_pressing_eleven_times_ends_the_script(self):
        for _ in range(11):
            self.prologue.advance()
        self.assertTrue(self.prologue.finished)

    def test_finished_is_false_while_a_later_phase_is_pending(self):
        self.prologue.advance()
        self.prologue.advance()
        self.assertFalse(self.prologue.finished)

    def test_reset_returns_to_the_first_phase(self):
        self.prologue.advance()
        self.prologue.advance()
        self.prologue.advance()
        self.prologue.reset()
        self.assertEqual(self.prologue.phase_index, 0)
        self.assertEqual(self.prologue.revealed, 0.0)
        self.assertFalse(self.prologue.finished)

    def test_update_after_finishing_a_phase_is_a_noop(self):
        self.prologue.skip()
        self.prologue.update(5.0)
        self.assertEqual(self.prologue.visible_lines(), self.prologue.phases[0])

    def test_partial_line_is_truncated_mid_word(self):
        prologue = Prologue([["abcdefghij"]])
        prologue.revealed = 4.0
        self.assertEqual(prologue.visible_lines(), ["abcd"])

    def test_empty_script_is_immediately_finished(self):
        self.assertTrue(Prologue([]).finished)
        self.assertFalse(Prologue([]).advance())

    def test_parse_phases_splits_on_blank_lines(self):
        parsed = parse_phases("one\ntwo\n\nthree\n\n\nfour")
        self.assertEqual(parsed, [["one", "two"], ["three"], ["four"]])

    def test_parse_phases_ignores_a_trailing_separator(self):
        self.assertEqual(parse_phases("only\n\n"), [["only"]])

    def test_shipped_text_parses_into_the_expected_phase_count(self):
        self.assertEqual(len(parse_phases(PROLOGUE_PATH.read_text(encoding="utf-8"))), 6)

    def test_text_is_drawn_inside_the_left_margin(self):
        self.surface.fill(BG_COLOR)
        self.prologue.skip()
        self.prologue.draw(self.surface, self.font)
        self.assertEqual(min(self.drawn_columns(self.surface)), MARGIN)

    def test_text_is_drawn_at_double_scale(self):
        text = "ABCDE"
        self.surface.fill(BG_COLOR)
        partial = Prologue([[text, "ZZZZZ"]])
        partial.revealed = float(len(text))
        partial.draw(self.surface, self.font)
        self.assertEqual(partial.visible_lines(), [text])
        above_prompts = self.surface.get_height() - PROMPT_MARGIN - 24
        drawn = self.drawn_columns(self.surface, y_stop=above_prompts)
        width = max(drawn) - min(drawn) + 1
        expected = self.font.size(text)[0] * TEXT_SCALE
        self.assertGreaterEqual(width, expected - 3)
        self.assertLessEqual(width, expected)

    def test_skip_all_lands_on_the_final_phase_fully_revealed(self):
        self.prologue.skip_all()
        self.assertEqual(self.prologue.phase_index, self.prologue.phase_count - 1)
        self.assertTrue(self.prologue.phase_finished)
        self.assertTrue(self.prologue.finished)

    def test_skip_all_on_an_empty_script_is_harmless(self):
        empty = Prologue([])
        empty.skip_all()
        self.assertEqual(empty.lines, [])
        self.assertEqual(empty.phase_index, 0)
        self.assertTrue(empty.finished)

    def test_the_prompt_sits_in_the_bottom_right_corner(self):
        self.surface.fill(BG_COLOR)
        for _ in range(self.prologue.phase_count):
            self.prologue.advance()
            self.prologue.draw(self.surface, self.font)
        width = self.font.size(PROMPT)[0] * TEXT_SCALE
        height = self.font.size(PROMPT)[1] * TEXT_SCALE
        self.assertLessEqual(width + 4, INTERNAL_WIDTH)
        self.assertLessEqual(height + 4, INTERNAL_HEIGHT)

    def test_the_prompt_cluster_hangs_together(self):
        script = Prologue([["x"]])
        script.skip_all()
        with patch("pygame.time.get_ticks", return_value=BLINK_INTERVAL_MS):
            runs = self.prompt_band_runs(script)
        edge = self.skip_x()
        left = [end for _, end in runs if end < edge]
        right = [start for start, _ in runs if start >= edge]
        self.assertTrue(left and right)
        self.assertLessEqual(min(right) - max(left) - 1, PROMPT_GAP)

    def test_both_prompts_blink_in_sync(self):
        script = Prologue([["x"]])
        script.skip_all()
        with patch("pygame.time.get_ticks", return_value=BLINK_INTERVAL_MS):
            lit = self.prompt_band_runs(script)
        with patch("pygame.time.get_ticks", return_value=0):
            dark = self.prompt_band_runs(script)
        self.assertTrue(lit)
        self.assertEqual(dark, [])

    def test_the_skip_prompt_stays_visible_while_typing(self):
        script = Prologue([["x"]])
        self.assertFalse(script.phase_finished)
        with patch("pygame.time.get_ticks", return_value=BLINK_INTERVAL_MS):
            runs = self.prompt_band_runs(script)
        edge = self.skip_x()
        self.assertTrue([start for start, _ in runs if start >= edge])
        self.assertFalse([start for start, _ in runs if start < edge])

    def test_the_skip_prompt_does_not_shift_when_enter_appears(self):
        typing = Prologue([["x"]])
        done = Prologue([["x"]])
        done.skip_all()
        edge = self.skip_x()
        with patch("pygame.time.get_ticks", return_value=BLINK_INTERVAL_MS):
            before = [start for start, _ in self.prompt_band_runs(typing) if start >= edge]
            after = [start for start, _ in self.prompt_band_runs(done) if start >= edge]
        self.assertEqual(before, after)

    def test_draw_does_not_crash_at_any_stage(self):
        for _ in range(30):
            self.prologue.update(1 / 60)
            self.prologue.draw(self.surface, self.font)
        for _ in range(self.prologue.phase_count * 2):
            self.prologue.advance()
            self.prologue.draw(self.surface, self.font)

    def test_every_phase_draws_without_crashing(self):
        for _ in range(self.prologue.phase_count * 2):
            self.prologue.advance()
            self.surface.fill(BG_COLOR)
            self.prologue.draw(self.surface, self.font)


if __name__ == "__main__":
    unittest.main()
