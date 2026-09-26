from pathlib import Path

import pygame

from src.audio import Audio
from src.flow import Flow
from src.overlay import CrtOverlay
from src.progression import Progress
from src.prologue import Prologue
from src.screens import Screens
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
from src.sprites import Sprites
from src.states import State

FONT_PATH = Path(__file__).parent / "assets" / "fonts" / "Px437_IBM_EGA_8x8.ttf"
# 8px is the 1:1 design size of the 8x8 font; other sizes break pixel crispness.
FONT_SIZE = 8

MOVE_KEYS = (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

TITLE_TEXT = "memLeak"
TITLE_RULE = "=" * 20
TITLE_TAGLINE = "you cannot un-leak a year"
TITLE_PROMPT = "PRESS ENTER TO BEGIN"


def load_font() -> pygame.font.Font:
    if FONT_PATH.is_file():
        return pygame.font.Font(str(FONT_PATH), FONT_SIZE)
    return pygame.font.SysFont("monospace", FONT_SIZE, bold=True)


MENU_STATES = (
    State.MENU,
    State.LEVEL_SELECT,
    State.SETTINGS,
    State.ACHIEVEMENTS,
)

MUSIC_FOR_STATE = {
    State.TITLE: "menu",
    State.MENU: "menu",
    State.LEVEL_SELECT: "menu",
    State.SETTINGS: "menu",
    State.ACHIEVEMENTS: "menu",
    State.PAUSED: "menu",
    State.PROLOGUE: "prologue",
    State.PLAY: "game",
    State.CLEARED: "game",
    State.GAMEOVER: "game",
}


def handle_key(
    key: int,
    state: State,
    session: Session,
    prologue: Prologue,
    flow: Flow | None = None,
    screens=None,
) -> State:
    if state is State.TITLE:
        if key in CONFIRM_KEYS:
            return State.PROLOGUE
    elif state is State.PROLOGUE:
        if key in CONFIRM_KEYS and not prologue.advance():
            if flow is not None:
                flow.progress.seen_prologue = True
                flow.progress.save()
            return State.PLAY
    elif state is State.PLAY:
        if key in MOVE_KEYS:
            session.press_step()
        elif key == pygame.K_SPACE:
            session.press_jump()
        elif key == pygame.K_ESCAPE:
            return State.PAUSED
    elif state is State.PAUSED:
        if screens is not None:
            result = screens.handle_key(state, key)
            return result if result is not None else state
        if key == pygame.K_ESCAPE:
            return State.PLAY
    elif state in (State.CLEARED, State.GAMEOVER):
        if key == pygame.K_r:
            if flow is not None:
                flow.restart()
            else:
                session.reset()
            return State.PLAY
        if key in CONFIRM_KEYS:
            if state is State.CLEARED and flow is not None:
                if flow.advance():
                    return State.PLAY
            elif flow is None:
                session.reset()
                return State.PLAY
    return state


def draw_centered(canvas, font, text, y, color) -> None:
    msg = font.render(text, False, color)
    canvas.blit(msg, (INTERNAL_WIDTH // 2 - msg.get_width() // 2, y))


def draw_title(canvas, font) -> None:
    draw_centered(canvas, font, TITLE_TEXT, 56, TARGET_COLOR)
    draw_centered(canvas, font, TITLE_RULE, 70, HAZARD_COLOR)
    draw_centered(canvas, font, TITLE_TAGLINE, 84, TEXT_COLOR)
    if int(pygame.time.get_ticks() / 500) % 2 == 0:
        draw_centered(canvas, font, TITLE_PROMPT, 108, TEXT_COLOR)


def render_world(
    canvas, chamber, session, state, font, sprites=None, flow=None, screens=None
) -> None:
    chamber.draw(canvas, session.falling, sprites)
    session.player.draw(canvas, sprites)

    hud = font.render(
        f"EARTH_ALLOC: {session.earth_alloc:06.1f} YRS  T:{session.elapsed:06.2f}s",
        False,
        TEXT_COLOR,
    )
    canvas.blit(hud, (4, 4))
    canvas.blit(font.render(chamber.level.name, False, TARGET_COLOR), (4, 13))

    if state is State.PAUSED:
        if screens is not None:
            screens.pause.draw(canvas, font, y=52)
        else:
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
        best_time, best_years = (
            flow.progress.best_for(flow.level_index) if flow else (0.0, 0.0)
        )
        draw_centered(
            canvas,
            font,
            f"BEST {best_time:.2f}s / {int(best_years)} YRS",
            82,
            TEXT_COLOR,
        )
        has_next = flow is not None and flow.level_index + 1 < flow.level_count
        draw_centered(
            canvas,
            font,
            "[ENTER] NEXT CHAMBER   [R] REPLAY" if has_next else "ALL CHAMBERS CLEARED",
            96,
            TEXT_COLOR,
        )


def render(
    canvas,
    chamber,
    session,
    state,
    font,
    prologue,
    sprites=None,
    flow=None,
    screens=None,
) -> None:
    canvas.fill(BG_COLOR)
    if state is State.TITLE:
        draw_title(canvas, font)
    elif state is State.PROLOGUE:
        prologue.draw(canvas, font)
    elif state in MENU_STATES and screens is not None:
        screens.draw(canvas, font, state)
    else:
        render_world(canvas, chamber, session, state, font, sprites, flow, screens)


def main() -> None:
    pygame.init()
    pygame.font.init()
    window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("memLeak")
    canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
    clock = pygame.time.Clock()
    font = load_font()

    flow = Flow(Progress())
    prologue = Prologue.from_file()
    audio = Audio()
    audio.music_volume = flow.progress.music_volume
    audio.sfx_volume = flow.progress.sfx_volume
    audio.muted = flow.progress.muted
    audio.apply_volumes()
    screens = Screens(flow, audio)
    sprites = Sprites()
    overlay = CrtOverlay(INTERNAL_WIDTH, INTERNAL_HEIGHT)
    state = State.MENU
    running = True
    frame_no = 0
    current_track = None

    while running:
        dt = clock.tick(FPS) / 1000.0
        if DEBUG:
            frame_no += 1
            print(
                f"FRAME {frame_no:>5} dt={dt:.4f} state={state.name} "
                f"alloc={flow.session.earth_alloc:8.2f} "
                f"on_ground={flow.session.player.on_ground!s:5} "
                f"rect.y={flow.session.player.rect.y:.3f}"
            )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                previous = state
                if state in MENU_STATES:
                    result = screens.handle_key(state, event.key)
                    if result is None:
                        running = False
                        continue
                    state = result
                else:
                    state = handle_key(
                        event.key, state, flow.session, prologue, flow, screens
                    )
                if state is State.PROLOGUE and previous is not State.PROLOGUE:
                    prologue.reset()

        if state is State.PROLOGUE:
            prologue.update(dt)
        elif state is State.PLAY:
            flow.session.step(dt, pygame.key.get_pressed())
            if flow.session.won:
                flow.record_win()
                state = State.CLEARED
            elif flow.session.game_over:
                state = State.GAMEOVER

        for cue in flow.session.drain_events():
            audio.play(cue)

        track = MUSIC_FOR_STATE.get(state)
        if track != current_track:
            current_track = track
            audio.play_music(track)

        render(
            canvas,
            flow.chamber,
            flow.session,
            state,
            font,
            prologue,
            sprites,
            flow,
            screens,
        )
        overlay.draw(canvas)
        window.blit(pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
