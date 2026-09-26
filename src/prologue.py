from pathlib import Path

import pygame

from src.settings import TARGET_COLOR, TEXT_COLOR

PROLOGUE_PATH = Path(__file__).resolve().parent.parent / "PROLOGUE.txt"
CHARS_PER_SECOND = 45.0
PROMPT = "[ENTER]"
PROMPT_MARGIN = 4
BLINK_INTERVAL_MS = 400
MAX_COLUMNS = 40


class Prologue:
    def __init__(self, lines, chars_per_second: float = CHARS_PER_SECOND) -> None:
        self.lines = list(lines)
        self.chars_per_second = chars_per_second
        self.revealed = 0.0
        self.total = sum(len(line) for line in self.lines) + max(
            0, len(self.lines) - 1
        )

    @classmethod
    def from_file(cls, path: Path = PROLOGUE_PATH) -> "Prologue":
        return cls(path.read_text(encoding="utf-8").splitlines())

    @property
    def finished(self) -> bool:
        return self.revealed >= self.total

    def update(self, dt: float) -> None:
        if not self.finished:
            self.revealed = min(
                float(self.total), self.revealed + self.chars_per_second * dt
            )

    def skip(self) -> None:
        self.revealed = float(self.total)

    def visible_lines(self) -> list[str]:
        remaining = int(self.revealed)
        shown: list[str] = []
        for line in self.lines:
            if remaining <= 0:
                break
            if remaining >= len(line):
                shown.append(line)
                remaining -= len(line) + 1
            else:
                shown.append(line[:remaining])
                remaining = 0
        return shown

    def draw(self, surface, font, color=TEXT_COLOR, prompt_color=TARGET_COLOR) -> None:
        leading = font.get_linesize()
        for index, line in enumerate(self.visible_lines()):
            if line:
                surface.blit(font.render(line, False, color), (0, index * leading))
        if self.finished and int(pygame.time.get_ticks() / BLINK_INTERVAL_MS) % 2:
            label = font.render(PROMPT, False, prompt_color)
            surface.blit(
                label,
                (surface.get_width() - label.get_width() - PROMPT_MARGIN, 0),
            )
