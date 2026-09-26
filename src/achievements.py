from dataclasses import dataclass

from src.levels import LEVELS, LevelDef


@dataclass(frozen=True)
class Achievement:
    key: str
    label: str
    hint: str


ACHIEVEMENTS = (
    Achievement("first_steps", "FIRST STEPS", "Clear OUTER HULL"),
    Achievement("clean_run", "CLEAN RUN", "Clear a chamber with no hits"),
    Achievement("speedster", "SPEEDSTER", "Clear a chamber under par time"),
    Achievement("deep_pocket", "DEEP POCKET", "Bank 500 years in one run"),
    Achievement("completionist", "COMPLETIONIST", "Clear all three chambers"),
)
BY_KEY = {achievement.key: achievement for achievement in ACHIEVEMENTS}
DEEP_POCKET_YEARS = 500.0


def earned_on_clear(
    level: LevelDef,
    elapsed: float,
    years: float,
    hits: int,
    already_cleared: bool,
    cleared_count: int,
) -> list[str]:
    keys: list[str] = []
    if level.index == 0 and not already_cleared:
        keys.append("first_steps")
    if hits == 0:
        keys.append("clean_run")
    if elapsed <= level.par_time:
        keys.append("speedster")
    if years >= DEEP_POCKET_YEARS:
        keys.append("deep_pocket")
    if cleared_count >= len(LEVELS):
        keys.append("completionist")
    return keys
