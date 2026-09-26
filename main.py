import sys

import pygame

from src.hazards import FallingHazard, next_interval, next_speed, spawn_x
from src.player import Player
from src.settings import (
    BG_COLOR,
    DRAIN_RATE,
    DEBUG,
    FPS,
    GROUND_COLOR,
    HAZARD_COLOR,
    HAZARD_PENALTY,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    JUMP_COST,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SPAWN_INTERVAL_MAX,
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
elapsed = 0.0
best_time = 0.0
best_saved = 0.0
falling: list[FallingHazard] = []
spawn_timer = SPAWN_INTERVAL_MAX

running = True
frame_no = 0
while running:
    dt = clock.tick(FPS) / 1000.0
    if DEBUG:
        frame_no += 1
        print(
            f"FRAME {frame_no:>5} dt={dt:.4f} vel_y={player.vel_y:8.2f} "
            f"on_ground={player.on_ground!s:5} rect.y={player.rect.y:.3f}"
        )

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
                elapsed = 0.0
                falling.clear()
                spawn_timer = SPAWN_INTERVAL_MAX
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
        elapsed += dt
        earth_alloc = max(0.0, earth_alloc - DRAIN_RATE * dt)
        if earth_alloc <= 0.0:
            game_over = True

        player.handle_input(pygame.key.get_pressed())
        player.update(dt, platforms)

        spawn_timer -= dt
        if spawn_timer <= 0.0:
            spawn_timer = next_interval(elapsed)
            falling.append(FallingHazard(spawn_x(player.rect.x), next_speed(elapsed)))
        for hz in falling:
            hz.update(dt)
        falling = [hz for hz in falling if not hz.is_spent()]

        # Check Hazard collisions
        struck = False
        for h in hazards:
            if player.rect.colliderect(h):
                struck = True
                break
        if not struck:
            for i, hz in enumerate(falling):
                if player.rect.colliderect(hz.rect):
                    del falling[i]
                    struck = True
                    break
        if struck:
            earth_alloc -= HAZARD_PENALTY
            # Respawn player at start of chamber
            player = Player(SPAWN_X, SPAWN_Y)
            if earth_alloc <= 0:
                earth_alloc = 0
                game_over = True

        # Check Target collision
        if player.rect.colliderect(target):
            won = True
            best_saved = max(best_saved, earth_alloc)
            if best_time == 0.0 or elapsed < best_time:
                best_time = elapsed

    # 3. Render
    canvas.fill(BG_COLOR)

    # Draw Platforms
    for p in platforms:
        pygame.draw.rect(canvas, GROUND_COLOR, p)

    # Draw Hazards
    for h in hazards:
        pygame.draw.rect(canvas, HAZARD_COLOR, h)
    for hz in falling:
        hz.draw(canvas)

    # Draw Target Portal
    pygame.draw.rect(canvas, TARGET_COLOR, target)

    # Draw Player
    player.draw(canvas)

    # Draw Terminal HUD
    hud_text = f"EARTH_ALLOC: {earth_alloc:06.1f} YRS  T:{elapsed:06.2f}s"
    hud_surface = font.render(hud_text, False, TEXT_COLOR)
    canvas.blit(hud_surface, (4, 4))

    # Win / Loss overlays
    if game_over:
        msg = font.render("KERNEL PANIC: TIMELINE HALTED [R to retry]", False, HAZARD_COLOR)
        canvas.blit(msg, (INTERNAL_WIDTH // 2 - msg.get_width() // 2, 70))
    elif won:
        msg = font.render(f"CLEARED IN {elapsed:.2f}s  SAVED {int(earth_alloc)} YRS", False, TARGET_COLOR)
        canvas.blit(msg, (INTERNAL_WIDTH // 2 - msg.get_width() // 2, 70))
        best = font.render(
            f"BEST {best_time:.2f}s / {int(best_saved)} YRS  [R to retry]", False, TEXT_COLOR
        )
        canvas.blit(best, (INTERNAL_WIDTH // 2 - best.get_width() // 2, 82))

    # Scale to window
    scaled = pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT))
    window.blit(scaled, (0, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()
