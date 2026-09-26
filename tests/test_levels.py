import os
import unittest
from dataclasses import replace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.chamber import Chamber
from src.hazards import MoverHazard, next_interval, next_speed
from src.levels import (
    LEVEL_ONE,
    LEVEL_THREE,
    LEVEL_TWO,
    LEVELS,
    RISE_BUDGET,
    SpawnProfile,
    level_at,
    validate_all,
    validate_level,
    widest_clear_floor,
)
from src.player import PLAYER_HEIGHT, PLAYER_WIDTH, Player
from src.session import Session


class NoKeys:
    def __getitem__(self, key):
        return False


class HoldRight(NoKeys):
    def __getitem__(self, key):
        return key in (pygame.K_RIGHT, pygame.K_d)


NO_KEYS = NoKeys()
RIGHT_KEYS = HoldRight()


def hop_is_feasible(level, src, dst, frames=260):
    """Can a player jump from `src` and land on `dst` without taking a hit?

    Sweeps the jump timing across a full run-up while holding right, which is
    the arc that has to work for a platform to be climbable.
    """
    chamber = Chamber(level)
    for jump_frame in range(1, 90):
        player = Player(src[0] + 1, src[1] - PLAYER_HEIGHT)
        for frame in range(frames):
            player.handle_input(RIGHT_KEYS)
            if frame == jump_frame:
                player.jump()
            player.update(1.0 / 60.0, chamber.platforms)
            if chamber.hits_hazard(player.rect):
                break
            if (
                player.on_ground
                and abs(player.rect.bottom - dst[1]) < 1
                and player.rect.right > dst[0]
                and player.rect.left < dst[0] + dst[2]
            ):
                return True
    return False


def target_is_reachable(level, src, frames=200):
    """Can a player walk off `src` and touch the gate?"""
    chamber = Chamber(level)
    player = Player(src[0] + 1, src[1] - PLAYER_HEIGHT)
    for _ in range(frames):
        player.handle_input(RIGHT_KEYS)
        player.update(1.0 / 60.0, chamber.platforms)
        if chamber.hits_hazard(player.rect):
            return False
        if chamber.reached_target(player.rect):
            return True
    return False


class LevelCatalogueTest(unittest.TestCase):
    def test_there_are_three_levels_with_unique_indices(self):
        self.assertEqual(len(LEVELS), 3)
        self.assertEqual([lvl.index for lvl in LEVELS], [0, 1, 2])
        self.assertEqual(
            [lvl.name for lvl in LEVELS], ["OUTER HULL", "CARGO SPINE", "CORE BREACH"]
        )

    def test_every_level_is_playable(self):
        self.assertEqual(validate_all(), [])

    def test_each_level_validates_individually(self):
        for level in LEVELS:
            self.assertEqual(validate_level(level), [], level.name)

    def test_difficulty_increases_monotonically(self):
        for earlier, later in zip(LEVELS, LEVELS[1:], strict=False):
            self.assertGreaterEqual(later.drain_rate, earlier.drain_rate)
            self.assertLessEqual(later.spawn.ramp_seconds, earlier.spawn.ramp_seconds)
            self.assertLessEqual(
                later.spawn.interval_min, earlier.spawn.interval_min
            )
        self.assertGreaterEqual(LEVEL_THREE.drain_rate, LEVEL_TWO.drain_rate)
        self.assertGreaterEqual(LEVEL_TWO.drain_rate, LEVEL_ONE.drain_rate)

    def test_harder_levels_add_obstacles(self):
        counts = [len(lvl.hazards) + len(lvl.movers) for lvl in LEVELS]
        self.assertEqual(counts, sorted(counts))
        self.assertEqual(LEVEL_ONE.movers, ())

    def test_every_rise_fits_the_jump_budget(self):
        for level in LEVELS:
            tops = sorted(p[1] for p in level.platforms)
            for lower, higher in zip(tops, tops[1:], strict=False):
                self.assertLessEqual(lower - higher, RISE_BUDGET, level.name)

    def test_level_at_clamps_out_of_range_indices(self):
        self.assertIs(level_at(-5), LEVELS[0])
        self.assertIs(level_at(99), LEVELS[-1])
        self.assertIs(level_at(1), LEVELS[1])

    def test_validator_rejects_an_unreachable_platform(self):
        broken = replace(LEVEL_ONE, platforms=LEVEL_ONE.platforms + ((300, 20, 20, 8),))
        self.assertTrue(
            any("unreachable" in p for p in validate_level(broken)),
            validate_level(broken),
        )

    def test_validator_rejects_a_target_overlapping_a_hazard(self):
        broken = replace(LEVEL_ONE, hazards=((260, 60, 14, 20),))
        self.assertTrue(
            any("overlaps" in p for p in validate_level(broken)),
            validate_level(broken),
        )

    def test_validator_rejects_geometry_off_screen(self):
        broken = replace(LEVEL_ONE, platforms=((0, 160, 400, 20),))
        self.assertTrue(
            any("outside" in p for p in validate_level(broken)),
            validate_level(broken),
        )

    def test_validator_rejects_a_spawn_inside_a_hazard(self):
        broken = replace(LEVEL_ONE, hazards=((16, 120, 20, 20),))
        self.assertTrue(
            any("spawn" in p for p in validate_level(broken)),
            validate_level(broken),
        )

    def test_validator_rejects_an_unsupported_target(self):
        broken = replace(LEVEL_ONE, target=(260, 10, 14, 20))
        self.assertTrue(
            any("resting" in p for p in validate_level(broken)),
            validate_level(broken),
        )


class CargoSpineTraversalTest(unittest.TestCase):
    """CARGO SPINE has to be climbable, not just valid.

    The wall on the third platform used to stand 44px tall. Clearing it needed
    a 44px rise, which took 0.197s of drift at walking speed -- 21.6px to the
    right -- but the ledge before the wall was only 15px wide, so the player
    was always carried into it. The hop simulation pins the fix.
    """

    def test_lower_platforms_can_be_climbed(self):
        ground, first, second, third, fourth = LEVEL_TWO.platforms
        self.assertTrue(hop_is_feasible(LEVEL_TWO, ground, first))
        self.assertTrue(hop_is_feasible(LEVEL_TWO, first, second))

    def test_the_wall_on_the_third_platform_can_be_cleared(self):
        _, _, _, third, fourth = LEVEL_TWO.platforms
        self.assertTrue(hop_is_feasible(LEVEL_TWO, third, fourth))

    def test_the_gate_is_reachable_from_the_top_platform(self):
        self.assertTrue(target_is_reachable(LEVEL_TWO, LEVEL_TWO.platforms[4]))

    def test_the_old_tall_wall_was_not_clearable(self):
        """Guards the guard: the sweep must be able to fail.

        Without this, a broken sweep would make the test above pass vacuously.
        """
        _, _, _, third, fourth = LEVEL_TWO.platforms
        broken = replace(
            LEVEL_TWO, hazards=LEVEL_TWO.hazards[:3] + ((192, 46, 10, 44),)
        )
        self.assertFalse(hop_is_feasible(broken, third, fourth))


class SpawnProfileTest(unittest.TestCase):
    def test_default_profile_matches_level_one(self):
        session_chamber = Chamber()
        self.assertEqual(session_chamber.spawn_profile, LEVEL_ONE.spawn)

    def test_interval_ramps_from_max_toward_min(self):
        profile = SpawnProfile(2.0, 0.5, 10.0, 80.0, 200.0)
        self.assertAlmostEqual(next_interval(0.0, profile), 2.0)
        self.assertAlmostEqual(next_interval(10.0, profile), 0.5)
        self.assertAlmostEqual(next_interval(999.0, profile), 0.5)

    def test_speed_ramps_from_min_toward_max(self):
        profile = SpawnProfile(2.0, 0.5, 10.0, 80.0, 200.0)
        self.assertAlmostEqual(next_speed(0.0, profile), 80.0)
        self.assertAlmostEqual(next_speed(10.0, profile), 200.0)

    def test_level_one_ramp_is_unchanged(self):
        self.assertAlmostEqual(next_interval(0.0), 2.5)
        self.assertAlmostEqual(next_interval(60.0), 0.8)
        self.assertAlmostEqual(next_speed(0.0), 70.0)
        self.assertAlmostEqual(next_speed(60.0), 190.0)


class MoverHazardTest(unittest.TestCase):
    def test_patrol_stays_inside_its_bounds(self):
        mover = MoverHazard((200, 150, 12, 10), 45.0, 195.0, 300.0)
        for _ in range(600):
            mover.update(1.0 / 60.0)
            self.assertGreaterEqual(mover.rect.x, 195.0)
            self.assertLessEqual(mover.rect.x + 12, 300.0)

    def test_direction_reverses_at_each_bound(self):
        mover = MoverHazard((200, 150, 12, 10), 45.0, 195.0, 300.0)
        mover.update(1.0)
        self.assertGreater(mover.rect.x, 200.0)
        mover.update(20.0)
        self.assertLess(mover.direction, 0.0)
        mover.update(40.0)
        self.assertGreater(mover.direction, 0.0)


class ChamberPerLevelTest(unittest.TestCase):
    def test_default_chamber_is_level_one(self):
        self.assertEqual(Chamber().level, LEVEL_ONE)

    def test_chamber_exposes_level_tuning(self):
        chamber = Chamber(LEVEL_THREE)
        self.assertEqual(chamber.drain_rate, LEVEL_THREE.drain_rate)
        self.assertEqual(chamber.start_years, LEVEL_THREE.start_years)
        self.assertEqual(chamber.spawn_profile, LEVEL_THREE.spawn)
        self.assertEqual(tuple(chamber.target), LEVEL_THREE.target)
        self.assertEqual(len(chamber.movers), len(LEVEL_THREE.movers))

    def test_session_uses_the_levels_drain_rate_and_starting_years(self):
        custom = replace(
            LEVEL_ONE, hazards=(), movers=(), drain_rate=100.0, start_years=500.0
        )
        session = Session(Chamber(custom))
        self.assertEqual(session.earth_alloc, 500.0)
        session.step(0.05, NO_KEYS)
        self.assertAlmostEqual(session.earth_alloc, 495.0, places=5)

    def test_session_reset_restores_movers_to_their_start(self):
        chamber = Chamber(LEVEL_THREE)
        session = Session(chamber)
        before = [mover.rect.x for mover in chamber.movers]
        for _ in range(120):
            session.step(1.0 / 60.0, NO_KEYS)
        session.reset()
        self.assertEqual([mover.rect.x for mover in chamber.movers], before)

    def test_every_level_renders(self):
        pygame.init()
        canvas = pygame.Surface((320, 180))
        for level in LEVELS:
            chamber = Chamber(level)
            session = Session(chamber)
            session.step(1.0 / 60.0, NO_KEYS)
            chamber.draw(canvas, session.falling)


class CoreBreachTraversalTest(unittest.TestCase):
    """CORE BREACH has to be standable, not merely valid.

    The spikes on the second and third platforms used to span 34px of a 42px
    platform, leaving 4px of clear floor at each end. The player is 12px wide,
    so it could not stand on either platform: every landing was a spike hit and
    the chamber could not be finished. The validator now enforces the clear
    floor invariant, and the last test proves that check can still fail.

    The hop sweep is deliberately not used here. It always spawns at a
    platform's left edge while holding right, which cannot land on a narrow
    platform nor touch a gate whose platform is spiked at that edge -- both are
    artefacts of the sweep, not blockers.
    """

    def test_every_platform_leaves_room_to_stand(self):
        for platform in LEVEL_THREE.platforms:
            gap = widest_clear_floor(platform, LEVEL_THREE.hazards)
            self.assertGreaterEqual(
                gap,
                PLAYER_WIDTH,
                f"platform {platform} leaves {gap}px of clear floor, "
                f"less than the {PLAYER_WIDTH}px player",
            )

    def test_the_middle_platforms_are_tighter_than_cargo_spine(self):
        """CORE BREACH must stay harder than the chamber before it."""
        _, _, breach_low, breach_high, _, _ = LEVEL_THREE.platforms
        _, _, spine_low, spine_high, _ = LEVEL_TWO.platforms
        for breach, spine in ((breach_low, spine_low), (breach_high, spine_high)):
            self.assertLess(
                widest_clear_floor(breach, LEVEL_THREE.hazards),
                widest_clear_floor(spine, LEVEL_TWO.hazards),
            )

    def test_the_lower_platforms_can_be_climbed(self):
        ground, first, second = LEVEL_THREE.platforms[:3]
        self.assertTrue(hop_is_feasible(LEVEL_THREE, ground, first))
        self.assertTrue(hop_is_feasible(LEVEL_THREE, first, second))

    def test_the_gate_is_reachable_from_the_top_platform(self):
        """Spawns inside the clear floor, since the platform's left edge is spiked."""
        chamber = Chamber(LEVEL_THREE)
        top = LEVEL_THREE.platforms[5]
        clear_from = widest_clear_floor(top, LEVEL_THREE.hazards)
        start = top[0] + top[2] - clear_from + PLAYER_WIDTH
        player = Player(start, top[1] - PLAYER_HEIGHT)
        for _ in range(200):
            player.handle_input(RIGHT_KEYS)
            player.update(1.0 / 60.0, chamber.platforms)
            self.assertFalse(chamber.hits_hazard(player.rect))
            if chamber.reached_target(player.rect):
                return
        self.fail("the gate was never reached from the top platform")

    def test_the_old_wide_spans_would_be_rejected(self):
        """Guards the guard: the clear floor check must be able to fail."""
        broken = replace(
            LEVEL_THREE,
            hazards=((44, 155, 30, 5), (96, 111, 34, 5), (150, 89, 34, 5)) + LEVEL_THREE.hazards[3:],
        )
        problems = validate_level(broken)
        self.assertTrue(
            any("clear floor" in problem for problem in problems),
            f"the 34px spans were not rejected: {problems}",
        )


if __name__ == "__main__":
    unittest.main()
