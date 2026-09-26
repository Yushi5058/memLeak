import random

import pygame

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


def ramp_ratio(elapsed: float) -> float:
    return min(elapsed / RAMP_SECONDS, 1.0)


def next_interval(elapsed: float) -> float:
    span = SPAWN_INTERVAL_MAX - SPAWN_INTERVAL_MIN
    return SPAWN_INTERVAL_MAX - span * ramp_ratio(elapsed)


def next_speed(elapsed: float) -> float:
    span = FALLING_HAZARD_SPEED_MAX - FALLING_HAZARD_SPEED_MIN
    return FALLING_HAZARD_SPEED_MIN + span * ramp_ratio(elapsed)


def spawn_x(avoid_x: float) -> float:
    x = random.uniform(0.0, INTERNAL_WIDTH - FALLING_HAZARD_WIDTH)
    if abs(x - avoid_x) < FALLING_HAZARD_WIDTH * 3:
        x = (x + INTERNAL_WIDTH / 2) % (INTERNAL_WIDTH - FALLING_HAZARD_WIDTH)
    return x


class FallingHazard:
    def __init__(self, x: float, speed: float):
        self.rect = pygame.FRect(x, -float(FALLING_HAZARD_HEIGHT), FALLING_HAZARD_WIDTH, FALLING_HAZARD_HEIGHT)
        self.vel_y = speed

    def update(self, dt: float) -> None:
        self.rect.y += self.vel_y * dt

    def is_spent(self) -> bool:
        return self.rect.top > INTERNAL_HEIGHT

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, HAZARD_COLOR, self.rect)
