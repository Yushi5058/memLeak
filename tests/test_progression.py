import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.flow import Flow
from src.levels import LEVELS
from src.progression import Progress
from src.settings import VOLUME_STEPS


class ProgressTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "save" / "progress.json"
        self.addCleanup(self.tmp.cleanup)

    def fresh(self) -> Progress:
        return Progress(self.path)

    def test_missing_file_starts_fresh(self):
        progress = self.fresh()
        self.assertEqual(progress.unlocked, 1)
        self.assertEqual(progress.cleared, [])
        self.assertEqual(progress.achievements, [])
        self.assertFalse(progress.is_unlocked(1))

    def test_record_clear_unlocks_the_next_level(self):
        progress = self.fresh()
        self.assertFalse(progress.is_unlocked(1))
        progress.record_clear(0, 12.5, 300.0)
        self.assertTrue(progress.is_unlocked(1))
        self.assertFalse(progress.is_unlocked(2))
        self.assertTrue(progress.has_cleared(0))

    def test_unlocks_are_capped_at_the_level_count(self):
        progress = self.fresh()
        progress.record_clear(len(LEVELS) - 1, 9.0, 100.0)
        self.assertEqual(progress.unlocked, len(LEVELS))
        self.assertFalse(progress.is_unlocked(len(LEVELS)))

    def test_best_records_keep_the_better_of_two_runs(self):
        progress = self.fresh()
        progress.record_clear(0, 20.0, 100.0)
        progress.record_clear(0, 15.0, 250.0)
        progress.record_clear(0, 30.0, 10.0)
        self.assertEqual(progress.best_for(0), (15.0, 250.0))

    def test_best_for_an_unplayed_level_is_zero(self):
        self.assertEqual(self.fresh().best_for(2), (0.0, 0.0))

    def test_state_survives_a_save_and_reload(self):
        progress = self.fresh()
        progress.record_clear(0, 11.0, 420.0)
        progress.unlock_achievement("first_steps")
        reloaded = self.fresh()
        self.assertEqual(reloaded.unlocked, 2)
        self.assertEqual(reloaded.best_for(0), (11.0, 420.0))
        self.assertTrue(reloaded.has_achievement("first_steps"))

    def test_achievement_unlocks_only_once(self):
        progress = self.fresh()
        self.assertTrue(progress.unlock_achievement("clean_run"))
        self.assertFalse(progress.unlock_achievement("clean_run"))
        self.assertTrue(self.fresh().has_achievement("clean_run"))

    def test_repeated_clears_do_not_duplicate_entries(self):
        progress = self.fresh()
        progress.record_clear(0, 12.0, 300.0)
        progress.record_clear(0, 14.0, 200.0)
        self.assertEqual(progress.cleared, [0])
        self.assertEqual(json.loads(self.path.read_text())["cleared"], [0])

    def test_corrupt_save_falls_back_to_defaults(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not json at all")
        progress = self.fresh()
        self.assertEqual(progress.unlocked, 1)
        self.assertEqual(progress.cleared, [])

    def test_non_dict_save_falls_back_to_defaults(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("[1, 2, 3]")
        self.assertEqual(self.fresh().unlocked, 1)

    def test_garbage_field_types_are_tolerated(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"unlocked": "nope", "cleared": "nope"}))
        progress = self.fresh()
        self.assertEqual(progress.unlocked, 1)
        self.assertEqual(progress.cleared, [])

    def test_saving_to_an_unwritable_location_never_raises(self):
        blocked = Path(self.tmp.name) / "blocked"
        blocked.write_text("i am a file, not a directory")
        progress = Progress(blocked / "nested" / "progress.json")
        progress.record_clear(0, 10.0, 50.0)
        self.assertTrue(progress.has_cleared(0))

    def test_writes_are_atomic_and_leave_no_temp_file(self):
        progress = self.fresh()
        progress.record_clear(0, 10.0, 50.0)
        siblings = list(self.path.parent.iterdir())
        self.assertEqual([p.name for p in siblings], ["progress.json"])


    def test_audio_settings_start_full_and_unmuted(self):
        progress = self.fresh()
        self.assertEqual(progress.music_volume, VOLUME_STEPS)
        self.assertEqual(progress.sfx_volume, VOLUME_STEPS)
        self.assertFalse(progress.muted)

    def test_audio_settings_survive_a_reload(self):
        progress = self.fresh()
        progress.set_audio_settings(2, 4, True)
        reloaded = self.fresh()
        self.assertEqual(reloaded.music_volume, 2)
        self.assertEqual(reloaded.sfx_volume, 4)
        self.assertTrue(reloaded.muted)

    def test_set_audio_settings_clamps_out_of_range_values(self):
        progress = self.fresh()
        progress.set_audio_settings(99, -4, False)
        self.assertEqual(progress.music_volume, VOLUME_STEPS)
        self.assertEqual(progress.sfx_volume, 0)
        self.assertEqual(self.fresh().music_volume, VOLUME_STEPS)
        self.assertEqual(self.fresh().sfx_volume, 0)

    def test_non_numeric_audio_values_fall_back_to_defaults(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"music_volume": "loud", "sfx_volume": None, "muted": "yes"}
            )
        )
        progress = self.fresh()
        self.assertEqual(progress.music_volume, VOLUME_STEPS)
        self.assertEqual(progress.sfx_volume, VOLUME_STEPS)
        self.assertTrue(progress.muted)

    def test_audio_settings_survive_alongside_progress(self):
        progress = self.fresh()
        progress.set_audio_settings(1, 1, True)
        progress.record_clear(0, 9.0, 400.0)
        reloaded = self.fresh()
        self.assertEqual(reloaded.music_volume, 1)
        self.assertTrue(reloaded.muted)
        self.assertTrue(reloaded.has_cleared(0))


class FlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "progress.json"
        self.addCleanup(self.tmp.cleanup)
        self.flow = Flow(Progress(self.path))

    def test_starts_on_level_one(self):
        self.assertEqual(self.flow.level_index, 0)
        self.assertEqual(self.flow.chamber.level, LEVELS[0])

    def test_start_selects_a_level_and_clamps(self):
        self.flow.start(2)
        self.assertEqual(self.flow.chamber.level, LEVELS[2])
        self.flow.start(99)
        self.assertEqual(self.flow.level_index, 2)
        self.flow.start(-4)
        self.assertEqual(self.flow.level_index, 0)

    def test_advance_walks_forward_and_stops_at_the_last_level(self):
        self.assertTrue(self.flow.advance())
        self.assertEqual(self.flow.level_index, 1)
        self.assertTrue(self.flow.advance())
        self.assertEqual(self.flow.level_index, 2)
        self.assertFalse(self.flow.advance())
        self.assertEqual(self.flow.level_index, 2)

    def test_restart_returns_to_the_same_level_with_a_fresh_run(self):
        self.flow.start(1)
        self.flow.session.elapsed = 12.0
        self.flow.restart()
        self.assertEqual(self.flow.level_index, 1)
        self.assertEqual(self.flow.session.elapsed, 0.0)
        self.assertFalse(self.flow.session.game_over)

    def test_record_win_persists_and_unlocks(self):
        self.flow.session.elapsed = 19.0
        self.flow.session.earth_alloc = 333.0
        self.flow.record_win()
        self.assertTrue(Progress(self.path).has_cleared(0))
        self.assertTrue(Progress(self.path).is_unlocked(1))

    def test_level_count_matches_the_catalogue(self):
        self.assertEqual(self.flow.level_count, len(LEVELS))


if __name__ == "__main__":
    unittest.main()
