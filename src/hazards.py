import random

import pygame

from src.levels import SpawnProfile
from src.settings import (
    FALLING_HAZARD_HEIGHT,
    FALLING_HAZARD_SPEED_MAX,
    FALLING_HAZARD_SPEED_MIN,
    FALLING_HAZARD_WIDTH,
    HAZARD_COLOR,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    RAMP_SECONDS,
    SPAWN_INTERVAL_MAX,
    SPAWN_INTERVAL_MIN,
)

DEFAULT_PROFILE = SpawnProfile(
    interval_max=SPAWN_INTERVAL_MAX,
    interval_min=SPAWN_INTERVAL_MIN,
    ramp_seconds=RAMP_SECONDS,
    speed_min=FALLING_HAZARD_SPEED_MIN,
    speed_max=FALLING_HAZARD_SPEED_MAX,
)


def ramp_ratio(elapsed: float, profile: SpawnProfile = DEFAULT_PROFILE) -> float:
    return min(elapsed / profile.ramp_seconds, 1.0)


def next_interval(elapsed: float, profile: SpawnProfile = DEFAULT_PROFILE) -> float:
    span = profile.interval_max - profile.interval_min
    return profile.interval_max - span * ramp_ratio(elapsed, profile)


def next_speed(elapsed: float, profile: SpawnProfile = DEFAULT_PROFILE) -> float:
    span = profile.speed_max - profile.speed_min
    return profile.speed_min + span * ramp_ratio(elapsed, profile)


def spawn_x(avoid_x: float) -> float:
    x = random.uniform(0.0, INTERNAL_WIDTH - FALLING_HAZARD_WIDTH)
    if abs(x - avoid_x) < FALLING_HAZARD_WIDTH * 3:
        x = (x + INTERNAL_WIDTH / 2) % (INTERNAL_WIDTH - FALLING_HAZARD_WIDTH)
    return x


class FallingHazard:
    def __init__(self, x: float, speed: float):
        self.rect = pygame.FRect(
            x, -float(FALLING_HAZARD_HEIGHT), FALLING_HAZARD_WIDTH, FALLING_HAZARD_HEIGHT
        )
        self.vel_y = speed

    def update(self, dt: float) -> None:
        self.rect.y += self.vel_y * dt

    def is_spent(self) -> bool:
        return self.rect.top > INTERNAL_HEIGHT

    def draw(self, surface: pygame.Surface, sprites=None) -> None:
        if sprites is not None:
            sprites.draw_sprite(surface, "hazard_falling", self.rect, HAZARD_COLOR)
        else:
            pygame.draw.rect(surface, HAZARD_COLOR, self.rect)


class MoverHazard:
    def __init__(self, rect, speed: float, x_min: float, x_max: float) -> None:
        self.rect = pygame.FRect(*rect)
        self.speed = speed
        self.x_min = x_min
        self.x_max = x_max
        self.direction = 1.0

    def update(self, dt: float) -> None:
        width = self.rect.width
        self.rect.x += self.speed * self.direction * dt
        if self.rect.x <= self.x_min:
            self.rect.x = self.x_min
            self.direction = 1.0
        elif self.rect.x + width >= self.x_max:
            self.rect.x = self.x_max - width
            self.direction = -1.0

    def draw(self, surface: pygame.Surface, sprites=None) -> None:
        if sprites is not None:
            sprites.draw_sprite(surface, "hazard_falling", self.rect, HAZARD_COLOR)
        else:
            pygame.draw.rect(surface, HAZARD_COLOR, self.rect)
