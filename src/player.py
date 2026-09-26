import pygame

from src.settings import (
    GRAVITY,
    INTERNAL_WIDTH,
    JUMP_STRENGTH,
    MOVE_SPEED,
    PLAYER_COLOR,
)

PLAYER_WIDTH = 12
PLAYER_HEIGHT = 16


class Player:
    def __init__(self, x: float, y: float):
        self.rect = pygame.FRect(float(x), float(y), PLAYER_WIDTH, PLAYER_HEIGHT)
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

    def update(self, dt: float, platforms: list[pygame.Rect]):
        # Apply Gravity
        self.vel_y += GRAVITY * dt

        # --- 1. Horizontal Movement & Collision ---
        self.rect.x += self.vel_x * dt

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > INTERNAL_WIDTH:
            self.rect.right = INTERNAL_WIDTH

        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_x > 0:
                    self.rect.right = plat.left
                elif self.vel_x < 0:
                    self.rect.left = plat.right

        # --- 2. Vertical Movement & Collision ---
        self.rect.y += self.vel_y * dt
        self.on_ground = False

        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_y > 0:  # Falling onto a surface
                    self.rect.bottom = plat.top
                    self.vel_y = 0.0
                    self.on_ground = True
                elif self.vel_y < 0:  # Hitting ceiling
                    self.rect.top = plat.bottom
                    self.vel_y = 0.0

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)
