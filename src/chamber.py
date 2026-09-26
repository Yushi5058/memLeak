from collections.abc import Sequence
from typing import TYPE_CHECKING

import pygame

from src.hazards import MoverHazard
from src.levels import LEVEL_ONE, LevelDef
from src.settings import GROUND_COLOR, HAZARD_COLOR, TARGET_COLOR

if TYPE_CHECKING:
    from src.hazards import FallingHazard


class Chamber:
    def __init__(self, level: LevelDef | None = None) -> None:
        self.level = level if level is not None else LEVEL_ONE
        self.platforms = [pygame.Rect(*r) for r in self.level.platforms]
        self.hazards = [pygame.Rect(*r) for r in self.level.hazards]
        self.movers = [
            MoverHazard(
                m.rect,
                m.speed,
                m.x_min,
                m.x_max,
                sprite_name=m.sprite_name,
                damage=m.damage,
            )
            for m in self.level.movers
        ]
        self.target = pygame.Rect(*self.level.target)
        self.spawn_point = self.level.spawn_point
        self.spawn_profile = self.level.spawn
        self.drain_rate = self.level.drain_rate
        self.start_years = self.level.start_years

    def reset(self) -> None:
        self.movers = [
            MoverHazard(
                m.rect,
                m.speed,
                m.x_min,
                m.x_max,
                sprite_name=m.sprite_name,
                damage=m.damage,
            )
            for m in self.level.movers
        ]

    def update(self, dt: float) -> None:
        for mover in self.movers:
            mover.update(dt)

    def hazard_damage(self, rect: pygame.FRect) -> float:
        if any(rect.colliderect(h) for h in self.hazards):
            return 1.0
        for m in self.movers:
            if rect.colliderect(m.rect):
                return m.damage
        return 0.0

    def hits_hazard(self, rect: pygame.FRect) -> bool:
        return self.hazard_damage(rect) > 0.0

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
        for mover in self.movers:
            mover.draw(surface, sprites)
        for hz in falling:
            hz.draw(surface, sprites)
        if sprites is not None:
            sprites.draw_sprite(surface, "portal", self.target, TARGET_COLOR)
        else:
            pygame.draw.rect(surface, TARGET_COLOR, self.target)
