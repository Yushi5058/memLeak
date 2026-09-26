from dataclasses import dataclass

from src.levels import LEVELS, LevelDef


@dataclass(frozen=True)
class Achievement:
    key: str
    label: str
    hint: str
    secret: bool = False


DEEP_POCKET_YEARS = 500.0
RAZOR_EDGE_YEARS = 25.0

ACHIEVEMENTS = (
    Achievement("first_steps", "FIRST STEPS", "Clear OUTER HULL"),
    Achievement("clean_run", "CLEAN RUN", "Clear a chamber with no hits"),
    Achievement("speedster", "SPEEDSTER", "Clear a chamber under par time"),
    Achievement("deep_pocket", "DEEP POCKET", "Bank 500 years in one run"),
    Achievement("completionist", "COMPLETIONIST", "Clear all three chambers"),
    Achievement(
        "razor_edge",
        "RAZOR EDGE",
        f"Clear a chamber with under {RAZOR_EDGE_YEARS:.0f} years left",
        secret=True,
    ),
    Achievement(
        "untouched",
        "UNTOUCHED",
        "Clear every chamber with no hits",
        secret=True,
    ),
)
BY_KEY = {achievement.key: achievement for achievement in ACHIEVEMENTS}


def visible_achievements(earned) -> tuple:
    """Achievements a player may see: the public ones, plus secrets already won.

    Keeps unearned secrets out of the list entirely, so neither their rows nor
    the total in the header reveal that they exist.
    """
    return tuple(
        a for a in ACHIEVEMENTS if not a.secret or a.key in earned
    )


def earned_on_clear(
    level: LevelDef,
    elapsed: float,
    years: float,
    hits: int,
    already_cleared: bool,
    cleared_count: int,
    clean_clear_count: int = 0,
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
    if years < RAZOR_EDGE_YEARS:
        keys.append("razor_edge")
    if clean_clear_count >= len(LEVELS):
        keys.append("untouched")
    return keys
