import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import main
from src.chapters import CHAPTER_PATHS, CHAPTER_TITLES, Narration, chapter_for
from src.flow import Flow
from src.levels import LEVELS
from src.progression import Progress
from src.prologue import MAX_COLUMNS, Prologue, parse_phases
from src.states import State


def walk(script: Prologue, narration: Narration, flow: Flow) -> State:
    """Presses confirm until the script hands control back to play."""
    state = State.PROLOGUE
    for _ in range(script.phase_count * 2):
        state = main.handle_key(
            pygame.K_RETURN, State.PROLOGUE, flow.session, narration, flow
        )
    return state


class ChapterTextTest(unittest.TestCase):
    def test_every_chamber_after_the_first_has_a_chapter(self):
        for index in range(1, len(LEVELS)):
            self.assertIn(index, CHAPTER_PATHS, index)
            self.assertIn(index, CHAPTER_TITLES, index)

    def test_the_first_chamber_has_no_chapter(self):
        self.assertIsNone(chapter_for(0))

    def test_chapter_lines_fit_the_prologue_width(self):
        for path in CHAPTER_PATHS.values():
            text = path.read_text(encoding="utf-8")
            self.assertTrue(parse_phases(text), path.name)
            for line in text.splitlines():
                self.assertLessEqual(
                    len(line.rstrip()), MAX_COLUMNS, f"{path.name}: {line!r}"
                )

    def test_chapters_carry_their_roman_numeral_title(self):
        for index, title in CHAPTER_TITLES.items():
            self.assertEqual(chapter_for(index).title, title)

    def test_a_chapter_is_not_empty(self):
        for index in CHAPTER_PATHS:
            self.assertGreaterEqual(chapter_for(index).phase_count, 2, index)


class PendingChapterTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "progress.json"
        self.flow = Flow(Progress(self.path))
        self.flow.start(0)

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_chamber_just_entered_gets_its_chapter(self):
        self.assertTrue(self.flow.advance())
        self.assertIs(self.flow.level_index, 1)
        self.assertIsNotNone(self.flow.pending_chapter())

    def test_the_first_chamber_is_introduced_by_the_prologue(self):
        self.flow.start(0)
        self.assertIsNone(self.flow.pending_chapter())

    def test_a_seen_chapter_is_not_offered_again(self):
        self.flow.advance()
        self.flow.mark_chapter_seen()
        self.assertIsNone(self.flow.pending_chapter())

    def test_marking_is_recorded_once(self):
        self.flow.advance()
        self.assertTrue(self.flow.mark_chapter_seen())
        self.assertFalse(self.flow.mark_chapter_seen())


class ChapterProgressTest(unittest.TestCase):
    def test_seen_chapters_survive_a_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            progress = Progress(path)
            progress.mark_chapter_seen(1)
            progress.mark_chapter_seen(2)
            reloaded = Progress(path)
            self.assertTrue(reloaded.has_seen_chapter(1))
            self.assertTrue(reloaded.has_seen_chapter(2))
            self.assertFalse(reloaded.has_seen_chapter(0))

    def test_a_corrupt_chapter_list_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text('{"seen_chapters": "nonsense"}')
            self.assertEqual(Progress(path).seen_chapters, [])

    def test_a_non_numeric_chapter_entry_is_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text('{"seen_chapters": [1, "two", -3]}')
            self.assertEqual(Progress(path).seen_chapters, [1])


class ChapterPlaybackTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "progress.json"
        self.flow = Flow(Progress(self.path))
        self.flow.start(0)
        self.narration = Narration(Prologue([["the prologue"]]))

    def tearDown(self):
        self._tmp.cleanup()

    def confirm(self, state: State) -> State:
        return main.handle_key(
            pygame.K_RETURN, state, self.flow.session, self.narration, self.flow
        )

    def test_advancing_into_a_chamber_plays_its_chapter_first(self):
        self.assertIs(self.confirm(State.CLEARED), State.PROLOGUE)
        self.assertTrue(self.narration.in_chapter)
        self.assertEqual(self.narration.active.title, CHAPTER_TITLES[1])

    def test_the_chapter_hands_control_back_to_play(self):
        self.confirm(State.CLEARED)
        self.assertIs(walk(self.narration.active, self.narration, self.flow), State.PLAY)
        self.assertFalse(self.narration.in_chapter)

    def test_the_chapter_is_remembered_but_does_not_mark_the_prologue(self):
        self.confirm(State.CLEARED)
        walk(self.narration.active, self.narration, self.flow)
        self.assertTrue(self.flow.progress.has_seen_chapter(1))
        self.assertFalse(self.flow.progress.seen_prologue)
        self.assertTrue(Progress(self.path).has_seen_chapter(1))

    def test_an_already_seen_chapter_does_not_replay(self):
        self.confirm(State.CLEARED)
        walk(self.narration.active, self.narration, self.flow)
        self.flow.start(0)
        self.assertIs(self.confirm(State.CLEARED), State.PLAY)
        self.assertFalse(self.narration.in_chapter)

    def test_the_next_chamber_gets_its_own_chapter(self):
        self.confirm(State.CLEARED)
        walk(self.narration.active, self.narration, self.flow)
        self.assertIs(self.confirm(State.CLEARED), State.PROLOGUE)
        self.assertEqual(self.narration.active.title, CHAPTER_TITLES[2])

    def test_replaying_the_current_chamber_never_shows_a_chapter(self):
        self.assertIs(
            main.handle_key(
                pygame.K_r, State.CLEARED, self.flow.session, self.narration, self.flow
            ),
            State.PLAY,
        )
        self.assertFalse(self.narration.in_chapter)

    def test_the_last_chamber_cannot_advance(self):
        self.flow.start(len(LEVELS) - 1)
        self.assertIs(self.confirm(State.CLEARED), State.CLEARED)


if __name__ == "__main__":
    unittest.main()
