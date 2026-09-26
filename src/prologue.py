from pathlib import Path

import pygame

from src.settings import TARGET_COLOR, TEXT_COLOR

PROLOGUE_PATH = Path(__file__).resolve().parent.parent / "PROLOGUE.txt"
CHARS_PER_SECOND = 22.0
PROMPT = "[ENTER]"
PROMPT_MARGIN = 4
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
    def __init__(self, phases, chars_per_second: float = CHARS_PER_SECOND) -> None:
        self.phases = [list(phase) for phase in phases]
        self.chars_per_second = chars_per_second
        self.index = 0
        self.revealed = 0.0

    @classmethod
    def from_file(cls, path: Path = PROLOGUE_PATH) -> "Prologue":
        return cls(parse_phases(path.read_text(encoding="utf-8")))

    @classmethod
    def from_text(cls, text: str) -> "Prologue":
        return cls(parse_phases(text))

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
        top = max(MARGIN, (surface.get_height() - leading * len(self.phases)) // 2)
        for index, line in enumerate(self.visible_lines()):
            if not line:
                continue
            stamp = font.render(line, False, color)
            scaled = pygame.transform.scale(
                stamp, (stamp.get_width() * TEXT_SCALE, stamp.get_height() * TEXT_SCALE)
            )
            surface.blit(scaled, (MARGIN, top + index * leading))
        if self.phase_finished and int(pygame.time.get_ticks() / BLINK_INTERVAL_MS) % 2:
            label = font.render(PROMPT, False, prompt_color)
            scaled = pygame.transform.scale(
                label, (label.get_width() * TEXT_SCALE, label.get_height() * TEXT_SCALE)
            )
            surface.blit(
                scaled,
                (
                    surface.get_width() - scaled.get_width() - PROMPT_MARGIN,
                    surface.get_height() - scaled.get_height() - PROMPT_MARGIN,
                ),
            )
