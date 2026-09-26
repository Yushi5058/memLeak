import pygame
from src.settings import (
    INTERNAL_WIDTH, GRAVITY, MOVE_SPEED, JUMP_STRENGTH, PLAYER_COLOR
)

class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.w = 12
        self.h = 16
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

    def handle_input(self, keys):
        self.vel_x = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -MOVE_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = MOVE_SPEED

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, dt: float, floor_y: float):
        # Apply gravity
        self.vel_y += GRAVITY * dt

        # Apply velocity
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt

        # Clamp horizontal boundaries
        if self.x < 0:
            self.x = 0
        elif self.x + self.w > INTERNAL_WIDTH:
            self.x = INTERNAL_WIDTH - self.w

        # Floor collision
        if self.y + self.h >= floor_y:
            self.y = floor_y - self.h
            self.vel_y = 0.0
            self.on_ground = True

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, PLAYER_COLOR, (int(self.x), int(self.y), self.w, self.h))
