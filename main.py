import sys

import pygame

from src.player import Player
from src.settings import (
    BG_COLOR,
    FPS,
    GROUND_COLOR,
    HAZARD_COLOR,
    HAZARD_PENALTY,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    JUMP_COST,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    START_EARTH_YEARS,
    STEP_COST,
    TARGET_COLOR,
    TEXT_COLOR,
)

pygame.init()
pygame.font.init()
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("memLeak")

canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 8, bold=True)

# Spawn point
SPAWN_X, SPAWN_Y = 20.0, 130.0
player = Player(SPAWN_X, SPAWN_Y)

# --- World Objects (Rects) ---
# Solid platforms: (x, y, width, height)
platforms = [
    pygame.Rect(0, 160, INTERNAL_WIDTH, 20),  # Main floor
    pygame.Rect(60, 130, 50, 10),  # Low platform
    pygame.Rect(140, 105, 50, 10),  # Mid platform
    pygame.Rect(220, 80, 60, 10),  # High ledge
]

# Hazards: touch = time penalty + reset position
hazards = [
    pygame.Rect(120, 155, 30, 5),  # Floor spikes
    pygame.Rect(195, 100, 10, 60),  # Vertical laser / barrier
]

# Target portal (reach to clear the chapter)
target = pygame.Rect(260, 60, 14, 20)

# Game State
earth_alloc = START_EARTH_YEARS
game_over = False
won = False

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    # 1. Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # Restart game
            if event.key == pygame.K_r and (game_over or won):
                earth_alloc = START_EARTH_YEARS
                player = Player(SPAWN_X, SPAWN_Y)
                game_over = False
                won = False
            # Gameplay actions (only if still active)
            elif not game_over and not won:
                # Discrete move : left / right press
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    earth_alloc -= STEP_COST
                # Discrete move : Jump press (only costs if actually jumping off the ground)
                if event.key == pygame.K_SPACE:
                    if player.on_ground:
                        player.jump()
                        earth_alloc -= JUMP_COST
                    # Check if that action depleted the remaining years
                    if earth_alloc <= 0:
                        earth_alloc = 0
                        game_over = True
    # 2. Per-frame simulation (must run every frame, not once per event)
    if not game_over and not won:
        player.handle_input(pygame.key.get_pressed())
        player.update(dt, platforms)

        # Check Hazard collisions
        for h in hazards:
            if player.rect.colliderect(h):
                earth_alloc -= HAZARD_PENALTY
                # Respawn player at start of chamber
                player = Player(SPAWN_X, SPAWN_Y)
                if earth_alloc <= 0:
                    earth_alloc = 0
                    game_over = True
                break

        # Check Target collision
        if player.rect.colliderect(target):
            won = True

    # 3. Render
    canvas.fill(BG_COLOR)

    # Draw Platforms
    for p in platforms:
        pygame.draw.rect(canvas, GROUND_COLOR, p)

    # Draw Hazards
    for h in hazards:
        pygame.draw.rect(canvas, HAZARD_COLOR, h)

    # Draw Target Portal
    pygame.draw.rect(canvas, TARGET_COLOR, target)

    # Draw Player
    player.draw(canvas)

    # Draw Terminal HUD
    hud_text = f"EARTH_ALLOC: {earth_alloc:06.1f} YRS"
    hud_surface = font.render(hud_text, False, TEXT_COLOR)
    canvas.blit(hud_surface, (4, 4))

    # Win / Loss overlays
    if game_over:
        msg = font.render("KERNEL PANIC: TIMELINE HALTED [R to retry]", False, HAZARD_COLOR)
        canvas.blit(msg, (INTERNAL_WIDTH // 2 - msg.get_width() // 2, 70))
    elif won:
        msg = font.render(
            f"CHAMBER DEALLOCATED! SAVED: {int(earth_alloc)} YRS [R]", False, TARGET_COLOR
        )
        canvas.blit(msg, (INTERNAL_WIDTH // 2 - msg.get_width() // 2, 70))

    # Scale to window
    scaled = pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT))
    window.blit(scaled, (0, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()
