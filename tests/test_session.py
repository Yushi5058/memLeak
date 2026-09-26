import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.chamber import Chamber
from src.hazards import FallingHazard
from src.player import PLAYER_HEIGHT
from src.session import Session
from src.settings import (
    DRAIN_RATE,
    HAZARD_PENALTY,
    INTERNAL_WIDTH,
    JUMP_COST,
    MAX_DT,
    START_EARTH_YEARS,
    STEP_COST,
)

DT = 1.0 / 60.0


class Keys:
    def __getitem__(self, key):
        return False


NO_KEYS = Keys()


def falling_at(x, y, speed=70.0):
    hz = FallingHazard(x, speed)
    hz.rect.topleft = (x, y)
    return hz


class SessionTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.session = Session(Chamber())
        self.spawn = self.session.chamber.spawn_point

    def settle(self):
        for _ in range(30):
            self.session.step(DT, NO_KEYS)
        self.assertTrue(self.session.player.on_ground)

    def test_starts_at_spawn_point_with_full_allocation(self):
        self.assertEqual(self.session.player.rect.x, self.spawn[0])
        self.assertEqual(self.session.player.rect.y, self.spawn[1])
        self.assertEqual(self.session.earth_alloc, START_EARTH_YEARS)
        self.assertEqual(self.session.elapsed, 0.0)
        self.assertFalse(self.session.game_over)
        self.assertFalse(self.session.won)

    def test_player_falls_to_the_floor_and_lands(self):
        self.settle()
        self.assertEqual(self.session.player.rect.y, 160 - PLAYER_HEIGHT)

    def test_dt_is_clamped_to_max_dt(self):
        self.session.step(10.0, NO_KEYS)
        self.assertAlmostEqual(self.session.elapsed, MAX_DT)

    def test_step_is_noop_once_game_over(self):
        self.session.game_over = True
        self.session.step(DT, NO_KEYS)
        self.assertEqual(self.session.elapsed, 0.0)

    def test_step_is_noop_once_won(self):
        self.session.won = True
        self.session.step(DT, NO_KEYS)
        self.assertEqual(self.session.elapsed, 0.0)

    def test_drain_eventually_triggers_game_over(self):
        needed = int(START_EARTH_YEARS / (DRAIN_RATE * MAX_DT)) + 10
        for _ in range(needed):
            self.session.step(MAX_DT, NO_KEYS)
        self.assertTrue(self.session.game_over)
        self.assertEqual(self.session.earth_alloc, 0.0)

    def test_jump_costs_only_when_grounded(self):
        self.settle()
        before = self.session.earth_alloc
        self.assertTrue(self.session.press_jump())
        self.assertAlmostEqual(self.session.earth_alloc, before - JUMP_COST)
        self.assertFalse(self.session.press_jump())
        self.assertAlmostEqual(self.session.earth_alloc, before - JUMP_COST)

    def test_depleted_jump_sets_game_over_and_clamps_to_zero(self):
        self.settle()
        self.session.earth_alloc = 1.0
        self.session.press_jump()
        self.assertTrue(self.session.game_over)
        self.assertEqual(self.session.earth_alloc, 0.0)

    def test_step_press_costs_allocation(self):
        before = self.session.earth_alloc
        self.session.press_step()
        self.assertAlmostEqual(self.session.earth_alloc, before - STEP_COST)

    def test_static_hazard_strike_applies_penalty_and_respawns(self):
        self.settle()
        self.session.player.rect.topleft = (125.0, 150.0)
        before = self.session.earth_alloc
        self.session.step(0.0, NO_KEYS)
        self.assertAlmostEqual(self.session.earth_alloc, before - HAZARD_PENALTY)
        self.assertEqual(self.session.player.rect.x, self.spawn[0])
        self.assertEqual(self.session.player.rect.y, self.spawn[1])

    def test_falling_hazard_strike_consumes_that_hazard(self):
        self.settle()
        self.session.player.rect.topleft = (200.0, 50.0)
        self.session.falling.append(falling_at(200.0, 50.0))
        before = self.session.earth_alloc
        self.session.step(0.0, NO_KEYS)
        self.assertAlmostEqual(self.session.earth_alloc, before - HAZARD_PENALTY)
        self.assertEqual(self.session.falling, [])
        self.assertEqual(self.session.player.rect.x, self.spawn[0])

    def test_static_hazard_takes_priority_over_falling(self):
        self.settle()
        self.session.player.rect.topleft = (125.0, 150.0)
        overlapping = falling_at(125.0, 150.0)
        self.session.falling.append(overlapping)
        self.session.step(0.0, NO_KEYS)
        self.assertIn(overlapping, self.session.falling)
        self.assertEqual(self.session.player.rect.x, self.spawn[0])

    def test_reaching_target_wins_and_records_best(self):
        self.settle()
        expected_elapsed = self.session.elapsed
        expected_saved = self.session.earth_alloc
        self.session.player.rect.topleft = (262.0, 62.0)
        self.session.step(0.0, NO_KEYS)
        self.assertTrue(self.session.won)
        self.assertAlmostEqual(self.session.best_time, expected_elapsed)
        self.assertAlmostEqual(self.session.best_saved, expected_saved)

    def test_player_stays_inside_screen_bounds(self):
        self.settle()
        self.session.player.rect.topleft = (float(INTERNAL_WIDTH) - 4.0, 40.0)
        self.session.player.vel_x = 500.0
        self.session.step(DT, Keys())
        self.assertLessEqual(self.session.player.rect.right, INTERNAL_WIDTH)

    def test_reset_clears_run_state_but_keeps_records(self):
        self.settle()
        self.session.player.rect.topleft = (262.0, 62.0)
        self.session.step(0.0, NO_KEYS)
        self.session.falling.append(falling_at(10.0, 20.0))
        self.session.game_over = True
        best_time = self.session.best_time
        best_saved = self.session.best_saved

        self.session.reset()

        self.assertEqual(self.session.earth_alloc, START_EARTH_YEARS)
        self.assertEqual(self.session.elapsed, 0.0)
        self.assertEqual(self.session.falling, [])
        self.assertFalse(self.session.game_over)
        self.assertFalse(self.session.won)
        self.assertEqual(self.session.player.rect.x, self.spawn[0])
        self.assertAlmostEqual(self.session.best_time, best_time)
        self.assertAlmostEqual(self.session.best_saved, best_saved)

    def test_hazards_spawn_over_time_and_cull_when_spent(self):
        for _ in range(200):
            self.session.step(MAX_DT, NO_KEYS)
        self.assertTrue(self.session.falling)
        self.session.falling[0].rect.y = 400.0
        self.session.step(0.0, NO_KEYS)
        self.assertFalse(any(h.is_spent() for h in self.session.falling))


if __name__ == "__main__":
    unittest.main()
