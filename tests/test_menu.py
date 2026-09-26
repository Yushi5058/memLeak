import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.achievements import ACHIEVEMENTS, BY_KEY, earned_on_clear
from src.levels import LEVEL_ONE, LEVELS
from src.menu import CONFIRM_KEYS, Menu

ITEMS = (
    {"label": "ONE", "action": "one"},
    {"label": "TWO", "action": "two"},
    {"label": "THREE", "action": "three"},
)


class MenuTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.canvas = pygame.Surface((320, 180))
        self.menu = Menu("TEST", [dict(item) for item in ITEMS])

    def test_starts_on_the_first_item(self):
        self.assertEqual(self.menu.current()["action"], "one")

    def test_move_down_and_up(self):
        self.menu.move_down()
        self.assertEqual(self.menu.current()["action"], "two")
        self.menu.move_up()
        self.assertEqual(self.menu.current()["action"], "one")

    def test_navigation_wraps_at_both_ends(self):
        self.menu.move_up()
        self.assertEqual(self.menu.current()["action"], "three")
        self.menu.move_down()
        self.assertEqual(self.menu.current()["action"], "one")

    def test_empty_menu_is_safe(self):
        empty = Menu("NONE", [])
        self.assertIsNone(empty.current())
        empty.move_down()
        empty.move_up()
        self.assertIsNone(empty.current())
        self.assertIsNone(empty.handle_key(pygame.K_RETURN))
        empty.draw(self.canvas, pygame.font.Font(None, 12))

    def test_confirm_returns_the_current_action(self):
        for key in CONFIRM_KEYS:
            menu = Menu("TEST", [dict(item) for item in ITEMS])
            self.assertEqual(menu.handle_key(key), "one")

    def test_disabled_items_do_not_activate(self):
        menu = Menu(
            "TEST",
            [
                {"label": "LOCKED", "action": "nope", "enabled": False},
                {"label": "OPEN", "action": "yes"},
            ],
        )
        self.assertIsNone(menu.handle_key(pygame.K_RETURN))
        menu.move_down()
        self.assertEqual(menu.handle_key(pygame.K_RETURN), "yes")

    def test_hidden_items_are_skipped(self):
        menu = Menu(
            "TEST",
            [
                {"label": "A", "action": "a"},
                {"label": "B", "action": "b", "visible": False},
                {"label": "C", "action": "c"},
            ],
        )
        self.assertEqual([i["label"] for i in menu.visible()], ["A", "C"])
        menu.move_down()
        self.assertEqual(menu.current()["action"], "c")

    def test_left_and_right_only_adjust_steppable_items(self):
        menu = Menu("TEST", [{"label": "MUSIC", "action": "music", "step": True}])
        self.assertTrue(menu.adjust(1))
        self.assertEqual(menu.items[0]["value"], 1)
        menu.handle_key(pygame.K_RIGHT)
        self.assertEqual(menu.items[0]["value"], 2)
        menu.handle_key(pygame.K_LEFT)
        self.assertEqual(menu.items[0]["value"], 1)

    def test_plain_items_ignore_adjustment(self):
        menu = Menu("TEST", [dict(ITEMS[0])])
        self.assertFalse(menu.adjust(1))
        self.assertNotIn("value", menu.items[0])

    def test_arrows_navigate_and_never_activate(self):
        self.assertIsNone(self.menu.handle_key(pygame.K_DOWN))
        self.assertEqual(self.menu.current()["action"], "two")
        self.assertIsNone(self.menu.handle_key(pygame.K_UP))
        self.assertEqual(self.menu.current()["action"], "one")

    def test_index_is_clamped_when_items_shrink(self):
        self.menu.index = 2
        self.menu.items.pop()
        self.assertEqual(self.menu.current()["action"], "two")

    def test_reset_returns_to_the_top(self):
        self.menu.move_down()
        self.menu.reset()
        self.assertEqual(self.menu.current()["action"], "one")

    def test_draw_renders_every_row_without_crashing(self):
        font = pygame.font.Font(None, 12)
        self.menu.draw(self.canvas, font)
        self.menu.draw(self.canvas, font, y=10, x=5)
        self.assertTrue(self.canvas.get_at((0, 0)))


class AchievementTest(unittest.TestCase):
    def test_every_achievement_is_in_the_lookup(self):
        self.assertEqual(len(BY_KEY), len(ACHIEVEMENTS))
        for achievement in ACHIEVEMENTS:
            self.assertIs(BY_KEY[achievement.key], achievement)
            self.assertTrue(achievement.label)
            self.assertTrue(achievement.hint)

    def test_a_perfect_first_clear_earns_four(self):
        keys = earned_on_clear(LEVEL_ONE, 10.0, 600.0, 0, False, 1)
        self.assertEqual(
            keys, ["first_steps", "clean_run", "speedster", "deep_pocket"]
        )

    def test_being_hit_blocks_clean_run(self):
        keys = earned_on_clear(LEVEL_ONE, 10.0, 600.0, 1, False, 1)
        self.assertNotIn("clean_run", keys)

    def test_slow_run_blocks_speedster(self):
        keys = earned_on_clear(LEVEL_ONE, 999.0, 600.0, 0, False, 1)
        self.assertNotIn("speedster", keys)

    def test_lean_run_blocks_deep_pocket(self):
        keys = earned_on_clear(LEVEL_ONE, 10.0, 12.0, 0, False, 1)
        self.assertNotIn("deep_pocket", keys)

    def test_replay_does_not_re_earn_first_steps(self):
        keys = earned_on_clear(LEVEL_ONE, 10.0, 600.0, 0, True, 1)
        self.assertNotIn("first_steps", keys)

    def test_completionist_needs_every_chamber(self):
        partial = earned_on_clear(LEVELS[-1], 10.0, 600.0, 0, True, 2)
        self.assertNotIn("completionist", partial)
        total = earned_on_clear(LEVELS[-1], 10.0, 600.0, 0, True, len(LEVELS))
        self.assertIn("completionist", total)

    def test_first_steps_only_applies_to_the_first_chamber(self):
        keys = earned_on_clear(LEVELS[1], 10.0, 600.0, 0, False, 2)
        self.assertNotIn("first_steps", keys)
