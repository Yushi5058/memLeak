import sys
import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    FPS, BG_COLOR, GROUND_COLOR
)
from src.player import Player

pygame.init()
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("memLeak")

canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
clock = pygame.time.Clock()

player = Player(40.0, 100.0)
FLOOR_Y = 160

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()

    player.handle_input(pygame.key.get_pressed())
    player.update(dt, FLOOR_Y)

    # Render
    canvas.fill(BG_COLOR)
    pygame.draw.rect(canvas, GROUND_COLOR, (0, FLOOR_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - FLOOR_Y))
    player.draw(canvas)

    scaled_surface = pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT))
    window.blit(scaled_surface, (0, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()
