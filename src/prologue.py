from pathlib import Path

import pygame

from src.settings import TARGET_COLOR, TEXT_COLOR

PROLOGUE_PATH = Path(__file__).resolve().parent.parent / "PROLOGUE.txt"
CHARS_PER_SECOND = 22.0
PROMPT = "[ENTER]"
SKIP_PROMPT = "[S] SKIP"
PROMPT_MARGIN = 4
PROMPT_GAP = 2
BLINK_INTERVAL_MS = 400
MAX_COLUMNS = 18
TEXT_SCALE = 2
MARGIN = 16


def parse_phases(text: str) -> list[list[str]]:
    phases: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line:
            current.append(line)
        elif current:
            phases.append(current)
            current = []
    if current:
        phases.append(current)
    return phases


class Prologue:
    def __init__(
        self, phases, chars_per_second: float = CHARS_PER_SECOND, title: str | None = None
    ) -> None:
        self.phases = [list(phase) for phase in phases]
        self.chars_per_second = chars_per_second
        self.title = title
        self.index = 0
        self.revealed = 0.0

    @classmethod
    def from_file(cls, path: Path = PROLOGUE_PATH, title: str | None = None) -> "Prologue":
        return cls(parse_phases(path.read_text(encoding="utf-8")), title=title)

    @classmethod
    def from_text(cls, text: str, title: str | None = None) -> "Prologue":
        return cls(parse_phases(text), title=title)

    @property
    def phase_count(self) -> int:
        return len(self.phases)

    @property
    def phase_index(self) -> int:
        return self.index

    @property
    def lines(self) -> list[str]:
        return self.phases[self.index] if self.phases else []

    @property
    def total(self) -> int:
        lines = self.lines
        return sum(len(line) for line in lines) + max(0, len(lines) - 1)

    @property
    def phase_finished(self) -> bool:
        return self.revealed >= self.total

    @property
    def finished(self) -> bool:
        return self.index >= len(self.phases) - 1 and self.phase_finished

    def reset(self) -> None:
        self.index = 0
        self.revealed = 0.0

    def update(self, dt: float) -> None:
        if not self.phase_finished:
            self.revealed = min(
                float(self.total), self.revealed + self.chars_per_second * dt
            )

    def skip(self) -> None:
        self.revealed = float(self.total)

    def skip_all(self) -> None:
        """Reveal the entire script at once, landing on its final phase."""
        if not self.phases:
            return
        self.index = len(self.phases) - 1
        self.revealed = float(self.total)

    @staticmethod
    def _scaled(surface):
        return pygame.transform.scale(
            surface,
            (surface.get_width() * TEXT_SCALE, surface.get_height() * TEXT_SCALE),
        )

    def advance(self) -> bool:
        if not self.phase_finished:
            self.skip()
            return True
        if self.index < len(self.phases) - 1:
            self.index += 1
            self.revealed = 0.0
            return True
        return False

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
        leading = font.get_linesize() * TEXT_SCALE
        top = max(
            MARGIN,
            (surface.get_height() - leading * (len(self.phases) + (1 if self.title else 0)))
            // 2,
        )
        if self.title:
            heading = self._scaled(font.render(self.title, False, prompt_color))
            surface.blit(heading, ((surface.get_width() - heading.get_width()) // 2, top))
            top += leading
        for index, line in enumerate(self.visible_lines()):
            if not line:
                continue
            stamp = self._scaled(font.render(line, False, color))
            surface.blit(stamp, (MARGIN, top + index * leading))

        baseline = surface.get_height() - PROMPT_MARGIN
        skip = self._scaled(font.render(SKIP_PROMPT, False, prompt_color))
        label = self._scaled(font.render(PROMPT, False, prompt_color))
        skip_x = surface.get_width() - skip.get_width() - PROMPT_MARGIN
        label_x = skip_x - label.get_width() - PROMPT_GAP
        if int(pygame.time.get_ticks() / BLINK_INTERVAL_MS) % 2:
            surface.blit(skip, (skip_x, baseline - skip.get_height()))
            if self.phase_finished:
                surface.blit(label, (label_x, baseline - label.get_height()))
