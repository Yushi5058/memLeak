import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.sprites import (
    ART_SCALE,
    ART_SIZES,
    HITBOX_SIZES,
    SPRITE_NAMES,
    TILE_NAMES,
    TILE_SIZES,
    Sprites,
)

ALL_NAMES = (*SPRITE_NAMES, *TILE_NAMES)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
MAGENTA = (255, 0, 255)


def make_png(path: Path, size: tuple[int, int], color) -> None:
    surface = pygame.Surface(size)
    surface.fill(color)
    pygame.image.save(surface, str(path))


class SpritesTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.canvas = pygame.Surface((64, 64))
        self.canvas.fill((0, 0, 0))

    def test_missing_dir_falls_back_to_every_name(self):
        sprites = Sprites(assets_dir=Path("/nonexistent/sprites"))
        self.assertEqual(sprites.missing(), list(ALL_NAMES))
        for name in ALL_NAMES:
            self.assertFalse(sprites.has(name), name)
            rect = pygame.Rect(0, 0, 8, 8)
            if name in TILE_NAMES:
                sprites.draw_tiled(self.canvas, name, rect, (255, 0, 0))
            else:
                sprites.draw_sprite(self.canvas, name, rect, (255, 0, 0))
        self.assertEqual(self.canvas.get_at((4, 4))[:3], (255, 0, 0))

    def test_drawing_without_fallback_color_never_raises(self):
        sprites = Sprites(assets_dir=Path("/nonexistent/sprites"))
        rect = pygame.Rect(0, 0, 4, 4)
        sprites.draw_sprite(self.canvas, "player", rect)
        sprites.draw_tiled(self.canvas, "tile_platform", rect)

    def test_present_sprite_is_blitted_and_has_is_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            for name in ALL_NAMES:
                make_png(sprites_dir / f"{name}.png", (4, 4), (0, 255, 0))
            sprites = Sprites(assets_dir=sprites_dir)
            self.assertEqual(sprites.missing(), [])
            self.assertTrue(all(sprites.has(name) for name in ALL_NAMES))
            sprites.draw_sprite(self.canvas, "player", pygame.Rect(0, 0, 8, 8))
        self.assertEqual(self.canvas.get_at((4, 4))[:3], (0, 255, 0))

    def test_sprite_is_centred_on_the_collision_rect(self):
        art_width, art_height = ART_SIZES["player"]
        hitbox = pygame.Rect(30, 30, *HITBOX_SIZES["player"])
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            make_png(sprites_dir / "player.png", ART_SIZES["player"], GREEN)
            sprites = Sprites(assets_dir=sprites_dir)
            sprites.draw_sprite(self.canvas, "player", hitbox)
        left = hitbox.center[0] - art_width // 2
        top = hitbox.center[1] - art_height // 2
        inside_art = (
            (left + 1, top + 1),
            hitbox.center,
            (left + art_width - 1, top + art_height - 1),
        )
        outside_art = ((left - 1, top - 1), (left + art_width, top + art_height))
        for point in inside_art:
            self.assertEqual(self.canvas.get_at(point)[:3], GREEN, point)
        for point in outside_art:
            self.assertEqual(self.canvas.get_at(point)[:3], BLACK, point)

    def test_art_is_authored_larger_than_its_hitbox(self):
        for name, (width, height) in HITBOX_SIZES.items():
            self.assertEqual(ART_SIZES[name], (width * ART_SCALE, height * ART_SCALE))
            self.assertGreater(width * ART_SCALE, width, name)
            self.assertGreater(height * ART_SCALE, height, name)

    def test_tile_sizes_are_positive(self):
        for name, (width, height) in TILE_SIZES.items():
            self.assertGreater(width, 0, name)
            self.assertGreater(height, 0, name)

    def test_tiling_covers_a_rect_larger_than_the_texture(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            make_png(sprites_dir / "tile_platform.png", (4, 4), (0, 0, 255))
            sprites = Sprites(assets_dir=sprites_dir)
            sprites.draw_tiled(self.canvas, "tile_platform", pygame.Rect(0, 0, 9, 7))
        for point in ((0, 0), (8, 0), (0, 6), (8, 6)):
            self.assertEqual(self.canvas.get_at(point)[:3], (0, 0, 255), point)

    def test_oversized_art_is_normalised_to_the_spec_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            make_png(sprites_dir / "player.png", (512, 683), GREEN)
            sprites = Sprites(assets_dir=sprites_dir)
            self.assertEqual(sprites.images["player"].get_size(), ART_SIZES["player"])

    def test_undersized_art_is_normalised_to_the_spec_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            make_png(sprites_dir / "portal.png", (7, 5), BLUE)
            sprites = Sprites(assets_dir=sprites_dir)
            self.assertEqual(sprites.images["portal"].get_size(), ART_SIZES["portal"])

    def test_tiles_are_normalised_to_their_tile_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            make_png(sprites_dir / "tile_platform.png", (64, 64), BLUE)
            sprites = Sprites(assets_dir=sprites_dir)
            self.assertEqual(
                sprites.images["tile_platform"].get_size(), TILE_SIZES["tile_platform"]
            )

    def test_exact_size_art_is_left_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            make_png(sprites_dir / "player.png", ART_SIZES["player"], GREEN)
            sprites = Sprites(assets_dir=sprites_dir)
            self.assertEqual(sprites.images["player"].get_size(), ART_SIZES["player"])

    def test_corrupt_png_degrades_to_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            sprites_dir = Path(tmp)
            (sprites_dir / "player.png").write_bytes(b"not a png")
            sprites = Sprites(assets_dir=sprites_dir)
            self.assertFalse(sprites.has("player"))
            sprites.draw_sprite(
                self.canvas, "player", pygame.Rect(0, 0, 8, 8), (255, 0, 255)
            )
        self.assertEqual(self.canvas.get_at((4, 4))[:3], (255, 0, 255))


if __name__ == "__main__":
    unittest.main()
