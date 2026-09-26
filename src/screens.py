
from src.achievements import ACHIEVEMENTS
from src.levels import LEVELS
from src.menu import BACK_KEYS, CONFIRM_KEYS, LEFT_KEYS, RIGHT_KEYS, Menu
from src.settings import DIM_COLOR, HAZARD_COLOR, TARGET_COLOR, TEXT_COLOR
from src.states import State

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

    def _adjust_selected(self, delta: int) -> None:
        item = self.settings.current() or {}
        if item.get("action") == "music":
            self.audio.adjust_music(delta)
        elif item.get("action") == "sfx":
            self.audio.adjust_sfx(delta)

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
        elif action == "back":
            return self.settings_origin
        self._sync_settings_labels()
        return State.SETTINGS

    def draw(self, canvas, font, state: State) -> None:
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
            self._draw_achievements(canvas, font)

    def _draw_achievements(self, canvas, font) -> None:
        progress = self.flow.progress
        earned = len(progress.achievements)
        title = font.render(
            f"ACHIEVEMENTS  {earned}/{len(ACHIEVEMENTS)}", False, TARGET_COLOR
        )
        canvas.blit(title, ((canvas.get_width() - title.get_width()) // 2, 24))
        y = 40
        for achievement in ACHIEVEMENTS:
            unlocked = progress.has_achievement(achievement.key)
            mark = "*" if unlocked else " "
            color = TEXT_COLOR if unlocked else DIM_COLOR
            canvas.blit(
                font.render(f"{mark} {achievement.label}", False, color), (40, y)
            )
            canvas.blit(
                font.render(achievement.hint, False, DIM_COLOR), (150, y)
            )
            y += 11
        self._hint(canvas, font, "ESC BACK")

    def _hint(self, canvas, font, text: str) -> None:
        msg = font.render(text, False, HAZARD_COLOR)
        canvas.blit(msg, ((canvas.get_width() - msg.get_width()) // 2, 160))
