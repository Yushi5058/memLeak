from pathlib import Path

import pygame

from src.audio import Audio
from src.chamber import Chamber
from src.overlay import CrtOverlay
from src.session import Session
from src.settings import (
    BG_COLOR,
    DEBUG,
    FPS,
    HAZARD_COLOR,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TARGET_COLOR,
    TEXT_COLOR,
)
from src.states import State

FONT_PATH = Path(__file__).parent / "assets" / "fonts" / "Px437_IBM_EGA_8x8.ttf"
# 8px is the 1:1 design size of the 8x8 font; other sizes break pixel crispness.
FONT_SIZE = 8

MOVE_KEYS = (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d)


def load_font() -> pygame.font.Font:
    if FONT_PATH.is_file():
        return pygame.font.Font(str(FONT_PATH), FONT_SIZE)
    return pygame.font.SysFont("monospace", FONT_SIZE, bold=True)


def handle_key(key: int, state: State, session: Session) -> State:
    if state is State.PLAY:
        if key in MOVE_KEYS:
            session.press_step()
        elif key == pygame.K_SPACE:
            session.press_jump()
        elif key == pygame.K_ESCAPE:
            return State.PAUSED
    elif state is State.PAUSED:
        if key == pygame.K_ESCAPE:
            return State.PLAY
    elif state in (State.CLEARED, State.GAMEOVER):
        if key == pygame.K_r:
            session.reset()
            return State.PLAY
    return state


def draw_centered(canvas, font, text, y, color) -> None:
    msg = font.render(text, False, color)
    canvas.blit(msg, (INTERNAL_WIDTH // 2 - msg.get_width() // 2, y))


def render(canvas, chamber, session, state, font) -> None:
    canvas.fill(BG_COLOR)
    chamber.draw(canvas, session.falling)
    session.player.draw(canvas)

    hud = font.render(
        f"EARTH_ALLOC: {session.earth_alloc:06.1f} YRS  T:{session.elapsed:06.2f}s",
        False,
        TEXT_COLOR,
    )
    canvas.blit(hud, (4, 4))

    if state is State.PAUSED:
        draw_centered(canvas, font, "PAUSED [ESC to resume]", 70, TEXT_COLOR)
    elif state is State.GAMEOVER:
        draw_centered(canvas, font, "TIMELINE HALTED [R to retry]", 70, HAZARD_COLOR)
    elif state is State.CLEARED:
        draw_centered(
            canvas,
            font,
            f"CLEARED IN {session.elapsed:.2f}s  SAVED {int(session.earth_alloc)} YRS",
            70,
            TARGET_COLOR,
        )
        draw_centered(
            canvas,
            font,
            f"BEST {session.best_time:.2f}s / {int(session.best_saved)} YRS  [R to retry]",
            82,
            TEXT_COLOR,
        )


def main() -> None:
    pygame.init()
    pygame.font.init()
    window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("memLeak")
    canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
    clock = pygame.time.Clock()
    font = load_font()

    chamber = Chamber()
    session = Session(chamber)
    audio = Audio()
    overlay = CrtOverlay(INTERNAL_WIDTH, INTERNAL_HEIGHT)
    state = State.PLAY
    running = True
    frame_no = 0

    while running:
        dt = clock.tick(FPS) / 1000.0
        if DEBUG:
            frame_no += 1
            print(
                f"FRAME {frame_no:>5} dt={dt:.4f} state={state.name} "
                f"alloc={session.earth_alloc:8.2f} on_ground={session.player.on_ground!s:5} "
                f"rect.y={session.player.rect.y:.3f}"
            )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                state = handle_key(event.key, state, session)

        if state is State.PLAY:
            session.step(dt, pygame.key.get_pressed())
            if session.won:
                state = State.CLEARED
            elif session.game_over:
                state = State.GAMEOVER

        for cue in session.drain_events():
            audio.play(cue)

        render(canvas, chamber, session, state, font)
        overlay.draw(canvas)
        window.blit(pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
