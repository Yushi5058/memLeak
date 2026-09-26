import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.overlay import CrtOverlay


def white_surface(width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((255, 255, 255))
    return surface


SCANLINE_STRIDE = 3


def first_unscanned_row(height, stride=SCANLINE_STRIDE):
    row = height // 2
    while row % stride == 0:
        row += 1
    return row


CENTRE_Y = first_unscanned_row(180)
WINDOW_CENTRE_Y = first_unscanned_row(540)


class CrtOverlayTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.overlay = CrtOverlay(320, 180)

    def test_builds_at_requested_size(self):
        self.assertEqual(self.overlay.surface.get_size(), (320, 180))

    def test_draw_does_not_reallocate_the_cached_surface(self):
        before = self.overlay.surface
        target = white_surface(320, 180)
        self.overlay.draw(target)
        self.assertIs(self.overlay.surface, before)

    def test_repeated_draws_are_idempotent(self):
        once = white_surface(320, 180)
        twice = white_surface(320, 180)
        self.overlay.draw(once)
        self.overlay.draw(twice)
        self.assertEqual(pygame.image.tobytes(once, "RGBA"), pygame.image.tobytes(twice, "RGBA"))

    def test_centre_stays_untouched_and_corners_darken(self):
        target = white_surface(320, 180)
        self.overlay.draw(target)
        self.assertEqual(tuple(target.get_at((160, CENTRE_Y))), (255, 255, 255, 255))
        self.assertLess(target.get_at((0, 0)).r, 255)

    def test_centre_is_brighter_than_corner(self):
        target = white_surface(320, 180)
        self.overlay.draw(target)
        centre = target.get_at((160, CENTRE_Y))
        corner = target.get_at((0, 0))
        self.assertGreater(centre.r + centre.g + centre.b, corner.r + corner.g + corner.b)

    def test_darkening_is_subtle_enough_to_read_text(self):
        target = white_surface(320, 180)
        self.overlay.draw(target)
        self.assertGreater(min(target.get_at((160, CENTRE_Y))), 250)
        self.assertGreater(min(target.get_at((160, 4))), 200)

    def test_scanline_rows_are_darker_than_neighbours(self):
        target = white_surface(320, 180)
        self.overlay.draw(target)
        self.assertLess(
            sum(target.get_at((160, 0))),
            sum(target.get_at((160, 1))),
        )

    def test_works_at_window_resolution(self):
        overlay = CrtOverlay(960, 540)
        target = white_surface(960, 540)
        overlay.draw(target)
        self.assertEqual(tuple(target.get_at((480, WINDOW_CENTRE_Y))), (255, 255, 255, 255))
        self.assertLess(target.get_at((0, 0)).r, 255)

    def test_odd_dimensions_do_not_crash(self):
        for width, height in ((1, 1), (3, 5), (17, 3), (321, 181)):
            overlay = CrtOverlay(width, height)
            target = white_surface(width, height)
            overlay.draw(target)
            self.assertEqual(overlay.surface.get_size(), (width, height))

    def test_zero_stride_is_clamped_instead_of_dividing_by_zero(self):
        overlay = CrtOverlay(320, 180, scanline_stride=0)
        target = white_surface(320, 180)
        overlay.draw(target)
        self.assertEqual(overlay.scanline_stride, 1)

    def test_out_of_range_alphas_are_clamped(self):
        overlay = CrtOverlay(64, 64, scanline_alpha=-50, vignette_alpha=9999)
        target = white_surface(64, 64)
        overlay.draw(target)
        self.assertEqual(tuple(target.get_at((32, 32))), (255, 255, 255, 255))
        self.assertEqual(tuple(target.get_at((0, 0))), (0, 0, 0, 255))

    def test_zero_alpha_leaves_frame_untouched(self):
        overlay = CrtOverlay(64, 64, scanline_alpha=0, vignette_alpha=0)
        target = white_surface(64, 64)
        overlay.draw(target)
        self.assertEqual(tuple(target.get_at((0, 0))), (255, 255, 255, 255))
        self.assertEqual(tuple(target.get_at((32, 32))), (255, 255, 255, 255))


if __name__ == "__main__":
    unittest.main()
