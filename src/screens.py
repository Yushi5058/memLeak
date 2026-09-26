
from src.achievements import visible_achievements
from src.levels import LEVELS
from src.menu import BACK_KEYS, CONFIRM_KEYS, LEFT_KEYS, RIGHT_KEYS, Menu
from src.settings import (
    DIM_COLOR,
    EARNED_TILE_COLOR,
    HAZARD_COLOR,
    LOCKED_TILE_COLOR,
    TARGET_COLOR,
    TEXT_COLOR,
)
from src.states import State


def _trim_to_ink(surface):
    """Crop rendered text to its glyphs so layout measures ink, not the line box.

    pygame-ce renders text without per-pixel alpha, so the empty rows of a
    tall font's surface are opaque rather than transparent and cannot be
    detected by colour. `get_bounding_rect` still reports the real ink box.
    """
    box = surface.get_bounding_rect()
    if not box.width or not box.height:
        return surface
    return surface.subsurface(box).copy()


MAIN_ITEMS = (
    {"label": "START", "action": "start"},
    {"label": "ACHIEVEMENTS", "action": "achievements"},
    {"label": "AUDIO SETTINGS", "action": "settings"},
    {"label": "EXIT", "action": "exit"},
)
PAUSE_ITEMS = (
    {"label": "RESUME", "action": "resume"},
    {"label": "AUDIO SETTINGS", "action": "settings"},
    {"label": "EXIT TO MAIN MENU", "action": "menu"},
)
SETTINGS_ITEMS = (
    {"label": "MUSIC", "action": "music"},
    {"label": "SOUND", "action": "sfx"},
    {"label": "MUTE ALL", "action": "mute"},
    {"label": "BACK", "action": "back"},
)


class Screens:
    def __init__(self, flow, audio) -> None:
        self.flow = flow
        self.audio = audio
        self.main = Menu("memLeak", [dict(item) for item in MAIN_ITEMS])
        self.pause = Menu("PAUSED", [dict(item) for item in PAUSE_ITEMS])
        self.settings = Menu("AUDIO SETTINGS", [dict(item) for item in SETTINGS_ITEMS])
        self.levels = Menu("SELECT CHAMBER", [])
        self.settings_origin = State.MENU
        self.achievements_origin = State.MENU

    def build_level_menu(self) -> None:
        progress = self.flow.progress
        items = []
        for level in LEVELS:
            unlocked = progress.is_unlocked(level.index)
            label = f"{level.index + 1}. {level.name}"
            best_time, best_years = progress.best_for(level.index)
            if best_time:
                label += f"  {best_time:.2f}s"
            if not unlocked:
                label += "  [LOCKED]"
            items.append(
                {
                    "label": label,
                    "action": f"play:{level.index}",
                    "enabled": unlocked,
                }
            )
        self.levels = Menu("SELECT CHAMBER", items)

    def _sync_settings_labels(self) -> None:
        self.settings.items[0]["value_label"] = self.audio.music_label
        self.settings.items[1]["value_label"] = self.audio.sfx_label
        self.settings.items[2]["label"] = f"MUTE ALL < {self.audio.mute_label} >"

    def _first_play_state(self) -> State:
        if self.flow.progress.seen_prologue:
            return State.PLAY
        return State.PROLOGUE

    def handle_key(self, state: State, key: int) -> State | None:
        if state is State.MENU:
            return self._handle_main(key)
        if state is State.LEVEL_SELECT:
            return self._handle_levels(key)
        if state is State.PAUSED:
            return self._handle_pause(key)
        if state is State.SETTINGS:
            return self._handle_settings(key)
        if state is State.ACHIEVEMENTS:
            if key in BACK_KEYS or key in CONFIRM_KEYS:
                return self.achievements_origin
            return state
        return state

    def _handle_main(self, key: int) -> State | None:
        if key in BACK_KEYS:
            return None
        action = self.main.handle_key(key)
        if action == "start":
            self.build_level_menu()
            return State.LEVEL_SELECT
        if action == "achievements":
            self.achievements_origin = State.MENU
            return State.ACHIEVEMENTS
        if action == "settings":
            self.settings_origin = State.MENU
            return State.SETTINGS
        if action == "exit":
            return None
        return State.MENU

    def _handle_levels(self, key: int) -> State:
        if key in BACK_KEYS:
            return State.MENU
        action = self.levels.handle_key(key)
        if action and action.startswith("play:"):
            self.flow.start(int(action.split(":")[1]))
            return self._first_play_state()
        return State.LEVEL_SELECT

    def _handle_pause(self, key: int) -> State:
        if key in BACK_KEYS:
            return State.PLAY
        action = self.pause.handle_key(key)
        if action == "resume":
            return State.PLAY
        if action == "settings":
            self.settings_origin = State.PAUSED
            return State.SETTINGS
        if action == "menu":
            return State.MENU
        return State.PAUSED

    def _persist_audio(self) -> None:
        self.flow.progress.set_audio_settings(
            self.audio.music_volume, self.audio.sfx_volume, self.audio.muted
        )

    def _adjust_selected(self, delta: int) -> None:
        item = self.settings.current() or {}
        if item.get("action") == "music":
            self.audio.adjust_music(delta)
        elif item.get("action") == "sfx":
            self.audio.adjust_sfx(delta)
        else:
            return
        self._persist_audio()

    def _handle_settings(self, key: int) -> State:
        if key in BACK_KEYS:
            return self.settings_origin
        if key in LEFT_KEYS:
            self._adjust_selected(-1)
        elif key in RIGHT_KEYS:
            self._adjust_selected(1)
        action = self.settings.handle_key(key)
        if action == "mute":
            self.audio.toggle_mute()
            self._persist_audio()
        elif action == "back":
            return self.settings_origin
        self._sync_settings_labels()
        return State.SETTINGS

    def draw(self, canvas, font, state: State, small_font=None) -> None:
        if state is State.MENU:
            self.main.draw(canvas, font, y=44)
            self._hint(canvas, font, "ARROWS MOVE   ENTER SELECT")
        elif state is State.LEVEL_SELECT:
            self.levels.draw(canvas, font, y=40)
            self._hint(canvas, font, "ESC BACK")
        elif state is State.PAUSED:
            self.pause.draw(canvas, font, y=44)
        elif state is State.SETTINGS:
            self._sync_settings_labels()
            self.settings.draw(canvas, font, y=40)
            self._hint(canvas, font, "LEFT/RIGHT ADJUST   ESC BACK")
        elif state is State.ACHIEVEMENTS:
            self._draw_achievements(canvas, font, small_font or font)

    def _draw_achievements(self, canvas, font, small_font) -> None:
        progress = self.flow.progress
        visible = visible_achievements(progress.achievements)
        earned = sum(1 for a in visible if progress.has_achievement(a.key))
        title = font.render(
            f"ACHIEVEMENTS  {earned}/{len(visible)}", False, TARGET_COLOR
        )
        self._centered(canvas, title, 22)

        rows = []
        for achievement in visible:
            unlocked = progress.has_achievement(achievement.key)
            mark = "*" if unlocked else " "
            color = TEXT_COLOR if unlocked else DIM_COLOR
            rows.append(
                (
                    unlocked,
                    _trim_to_ink(font.render(f"{mark} {achievement.label}", False, color)),
                    _trim_to_ink(
                        small_font.render(achievement.hint, False, DIM_COLOR)
                    ),
                )
            )

        label_w = max(r[1].get_width() for r in rows)
        hint_w = max(r[2].get_width() for r in rows)
        gap = 6
        pad = 6
        tile_w = label_w + gap + hint_w + pad * 2
        tile_x = (canvas.get_width() - tile_w) // 2
        row_h = (
            max(max(r[1].get_height() for r in rows), max(r[2].get_height() for r in rows))
            + 4
        )
        pitch = row_h + 3
        y = 40
        for unlocked, label, hint in rows:
            canvas.fill(
                EARNED_TILE_COLOR if unlocked else LOCKED_TILE_COLOR,
                (tile_x, y, tile_w, row_h),
            )
            label_x = tile_x + pad + (label_w - label.get_width())
            hint_x = tile_x + pad + label_w + gap
            text_y = y + (row_h - hint.get_height()) // 2
            canvas.blit(label, (label_x, y + (row_h - label.get_height()) // 2))
            canvas.blit(hint, (hint_x, text_y))
            y += pitch
        self._hint(canvas, font, "ESC BACK")

    def _centered(self, canvas, surface, y: int) -> None:
        canvas.blit(surface, ((canvas.get_width() - surface.get_width()) // 2, y))

    def _hint(self, canvas, font, text: str) -> None:
        self._centered(canvas, font.render(text, False, HAZARD_COLOR), 160)
