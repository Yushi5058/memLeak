from pathlib import Path

import pygame

from src.settings import (
    GROUND_COLOR,
    HAZARD_COLOR,
    PLAYER_COLOR,
    TARGET_COLOR,
)

DEFAULT_SPRITES_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"
SPRITE_NAMES = ("player", "hazard_falling", "portal")
TILE_NAMES = ("tile_platform", "tile_hazard")

ART_SCALE = 2
HITBOX_SIZES = {
    "player": (12, 16),
    "hazard_falling": (10, 14),
    "portal": (14, 20),
}
ART_SIZES = {
    name: (width * ART_SCALE, height * ART_SCALE) for name, (width, height) in HITBOX_SIZES.items()
}
TILE_SIZES = {"tile_platform": (16, 16), "tile_hazard": (8, 8)}

FALLBACK_COLORS = {
    "player": PLAYER_COLOR,
    "tile_platform": GROUND_COLOR,
    "tile_hazard": HAZARD_COLOR,
    "hazard_falling": HAZARD_COLOR,
    "portal": TARGET_COLOR,
}


class Sprites:
    def __init__(self, assets_dir: Path | None = None) -> None:
        self.dir = Path(assets_dir) if assets_dir else DEFAULT_SPRITES_DIR
        self.images: dict[str, pygame.Surface] = {}
        for name in (*SPRITE_NAMES, *TILE_NAMES):
            target = ART_SIZES.get(name) or TILE_SIZES.get(name)
            image = self._load(self.dir / f"{name}.png", target)
            if image is not None:
                self.images[name] = image

    @staticmethod
    def _load(path: Path, target: tuple[int, int] | None) -> pygame.Surface | None:
        if not path.is_file():
            return None
        try:
            image = pygame.image.load(str(path))
        except pygame.error:
            return None
        try:
            image = image.convert_alpha()
        except pygame.error:
            pass
        if target is None or image.get_size() == target:
            return image
        shrinking = image.get_width() >= target[0] and image.get_height() >= target[1]
        resample = pygame.transform.smoothscale if shrinking else pygame.transform.scale
        try:
            return resample(image, target)
        except pygame.error:
            return image

    def has(self, name: str) -> bool:
        return name in self.images

    def missing(self) -> list[str]:
        return [name for name in (*SPRITE_NAMES, *TILE_NAMES) if name not in self.images]

    def draw_sprite(self, surface, name, rect, fallback=None) -> None:
        image = self.images.get(name)
        if image is None:
            pygame.draw.rect(surface, fallback or FALLBACK_COLORS[name], rect)
            return
        surface.blit(image, image.get_rect(center=(int(rect.centerx), int(rect.centery))))

    def draw_tiled(self, surface, name, rect, fallback=None) -> None:
        image = self.images.get(name)
        if image is None:
            pygame.draw.rect(surface, fallback or FALLBACK_COLORS[name], rect)
            return
        width, height = image.get_size()
        for y in range(rect.top, rect.bottom, height):
            for x in range(rect.left, rect.right, width):
                surface.blit(image, (x, y))
