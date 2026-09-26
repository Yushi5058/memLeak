import pygame

from src.settings import DIM_COLOR, HAZARD_COLOR, TEXT_COLOR

UP_KEYS = (pygame.K_UP, pygame.K_k)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_j)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_h)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_l)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BACK_KEYS = (pygame.K_ESCAPE, pygame.K_BACKSPACE)

ROW_HEIGHT = 12
CURSOR = ">"
PADDING = " "


class Menu:
    def __init__(self, title: str, items: list[dict]) -> None:
        self.title = title
        self.items = list(items)
        self.index = 0

    def reset(self) -> None:
        self.index = 0

    def visible(self) -> list[dict]:
        return [item for item in self.items if item.get("visible", True)]

    def _clamp(self) -> list[dict]:
        items = self.visible()
        self.index = max(0, min(self.index, len(items) - 1))
        return items

    def current(self) -> dict | None:
        items = self._clamp()
        return items[self.index] if items else None

    def move(self, delta: int) -> None:
        items = self._clamp()
        if items:
            self.index = (self.index + delta) % len(items)

    def move_up(self) -> None:
        self.move(-1)

    def move_down(self) -> None:
        self.move(1)

    def adjust(self, delta: int) -> bool:
        item = self.current()
        if item is None or not item.get("step"):
            return False
        item["value"] = item.get("value", 0) + delta
        return True

    def handle_key(self, key: int) -> str | None:
        if key in UP_KEYS:
            self.move_up()
        elif key in DOWN_KEYS:
            self.move_down()
        elif key in LEFT_KEYS:
            self.adjust(-1)
        elif key in RIGHT_KEYS:
            self.adjust(1)
        elif key in CONFIRM_KEYS:
            item = self.current()
            if item is not None and item.get("enabled", True):
                return item.get("action")
        return None

    def draw(self, canvas, font, y: int = 46, x: int | None = None) -> None:
        if self.title:
            title = font.render(self.title, False, HAZARD_COLOR)
            canvas.blit(title, ((canvas.get_width() - title.get_width()) // 2, y))
            y += ROW_HEIGHT + 4
        left = x if x is not None else max(8, canvas.get_width() // 2 - 70)
        for i, item in enumerate(self.visible()):
            color = TEXT_COLOR if item.get("enabled", True) else DIM_COLOR
            if "value_label" in item:
                body = f"{item['label']} < {item['value_label']} >"
            else:
                body = item["label"]
            cursor = CURSOR if i == self.index else PADDING
            canvas.blit(font.render(f"{cursor}{body}", False, color), (left, y))
            y += ROW_HEIGHT
