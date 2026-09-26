from collections.abc import Sequence
from typing import TYPE_CHECKING

import pygame

from src.settings import GROUND_COLOR, HAZARD_COLOR, INTERNAL_WIDTH, TARGET_COLOR

if TYPE_CHECKING:
    from src.hazards import FallingHazard


class Chamber:
    def __init__(self) -> None:
        self.platforms = [
            pygame.Rect(0, 160, INTERNAL_WIDTH, 20),
            pygame.Rect(60, 130, 50, 10),
            pygame.Rect(140, 105, 50, 10),
            pygame.Rect(220, 80, 60, 10),
        ]
        self.hazards = [
            pygame.Rect(120, 155, 30, 5),
            pygame.Rect(195, 100, 10, 60),
        ]
        self.target = pygame.Rect(260, 60, 14, 20)
        self.spawn_point = (20.0, 130.0)

    def hits_hazard(self, rect: pygame.FRect) -> bool:
        return any(rect.colliderect(h) for h in self.hazards)

    def reached_target(self, rect: pygame.FRect) -> bool:
        return rect.colliderect(self.target)

    def draw(
        self, surface: pygame.Surface, falling: Sequence["FallingHazard"], sprites=None
    ) -> None:
        for p in self.platforms:
            if sprites is not None:
                sprites.draw_tiled(surface, "tile_platform", p, GROUND_COLOR)
            else:
                pygame.draw.rect(surface, GROUND_COLOR, p)
        for h in self.hazards:
            if sprites is not None:
                sprites.draw_tiled(surface, "tile_hazard", h, HAZARD_COLOR)
            else:
                pygame.draw.rect(surface, HAZARD_COLOR, h)
        for hz in falling:
            hz.draw(surface, sprites)
        if sprites is not None:
            sprites.draw_sprite(surface, "portal", self.target, TARGET_COLOR)
        else:
            pygame.draw.rect(surface, TARGET_COLOR, self.target)
