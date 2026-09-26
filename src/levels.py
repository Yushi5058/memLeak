from dataclasses import dataclass

from src.player import PLAYER_WIDTH
from src.settings import (
    FALLING_HAZARD_SPEED_MAX,
    FALLING_HAZARD_SPEED_MIN,
    GRAVITY,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    JUMP_STRENGTH,
    MOVE_SPEED,
    RAMP_SECONDS,
    SPAWN_INTERVAL_MAX,
    SPAWN_INTERVAL_MIN,
)

Rect4 = tuple[int, int, int, int]

MAX_JUMP_RISE = JUMP_STRENGTH * JUMP_STRENGTH / (2.0 * GRAVITY)
AIR_TIME = 2.0 * abs(JUMP_STRENGTH) / GRAVITY
MAX_JUMP_REACH = MOVE_SPEED * AIR_TIME
RISE_BUDGET = MAX_JUMP_RISE * 0.8
REACH_BUDGET = MAX_JUMP_REACH * 0.8
SPAWN_CLEARANCE = 20


@dataclass(frozen=True)
class SpawnProfile:
    interval_max: float
    interval_min: float
    ramp_seconds: float
    speed_min: float
    speed_max: float


@dataclass(frozen=True)
class MoverDef:
    rect: Rect4
    speed: float
    x_min: float
    x_max: float
    sprite_name: str = "hazard_moving"
    damage: float = 1.0


@dataclass(frozen=True)
class LevelDef:
    index: int
    name: str
    blurb: str
    platforms: tuple[Rect4, ...]
    hazards: tuple[Rect4, ...]
    movers: tuple[MoverDef, ...]
    target: Rect4
    spawn_point: tuple[float, float]
    spawn: SpawnProfile
    drain_rate: float
    start_years: float
    par_time: float

    @property
    def obstacles(self) -> tuple[Rect4, ...]:
        return self.hazards + tuple(m.rect for m in self.movers)


LEVEL_ONE = LevelDef(
    index=0,
    name="OUTER HULL",
    blurb="Training run. Learn to spend time.",
    platforms=(
        (0, 160, 320, 20),
        (60, 130, 50, 10),
        (140, 105, 50, 10),
        (220, 80, 60, 10),
    ),
    hazards=(
        (120, 155, 30, 5),
        (195, 100, 10, 60),
    ),
    movers=(),
    target=(260, 60, 14, 20),
    spawn_point=(20.0, 130.0),
    spawn=SpawnProfile(
        interval_max=SPAWN_INTERVAL_MAX,
        interval_min=SPAWN_INTERVAL_MIN,
        ramp_seconds=RAMP_SECONDS,
        speed_min=FALLING_HAZARD_SPEED_MIN,
        speed_max=FALLING_HAZARD_SPEED_MAX,
    ),
    drain_rate=6.0,
    start_years=500.0,
    par_time=30.0,
)

LEVEL_TWO = LevelDef(
    index=1,
    name="CARGO SPINE",
    blurb="Deeper in. The air itself costs you.",
    platforms=(
        (0, 160, 320, 20),
        (45, 134, 48, 8),
        (105, 112, 48, 8),
        (165, 90, 48, 8),
        (225, 68, 60, 8),
    ),
    hazards=(
        (60, 155, 26, 5),
        (110, 107, 22, 5),
        (150, 152, 24, 5),
        (192, 74, 10, 16),
    ),
    movers=(
        # Time-infected robot
        MoverDef(
            rect=(200, 150, 12, 10),
            speed=30.0,
            x_min=195.0,
            x_max=300.0,
            sprite_name="hazard_moving",
            damage=1.0,
        ),
    ),
    target=(270, 48, 14, 20),
    spawn_point=(16.0, 120.0),
    spawn=SpawnProfile(2.0, 0.7, 50.0, 85.0, 210.0),
    drain_rate=9.0,
    start_years=440.0,
    par_time=32.0,
)

LEVEL_THREE = LevelDef(
    index=2,
    name="CORE BREACH",
    blurb="No margin left. Spend nothing.",
    platforms=(
        (0, 160, 320, 20),
        (38, 138, 42, 8),
        (92, 116, 42, 8),
        (146, 94, 42, 8),
        (200, 72, 42, 8),
        (250, 50, 60, 8),
    ),
    hazards=(
        (44, 155, 30, 5),
        (92, 111, 24, 5),
        (146, 89, 24, 5),
        (250, 45, 24, 5),
        (138, 104, 10, 56),
    ),
    movers=(
        # Time-infected robot
        MoverDef(
            rect=(100, 150, 12, 10),
            speed=45.0,
            x_min=95.0,
            x_max=180.0,
            sprite_name="hazard_moving",
            damage=1.0,
        ),
        # Gravitational singularity / black hole
        MoverDef(
            rect=(240, 146, 14, 14),
            speed=55.0,
            x_min=235.0,
            x_max=305.0,
            sprite_name="hazard_blackhole",
            damage=1.0,
        ),
    ),
    target=(280, 30, 14, 20),
    spawn_point=(14.0, 140.0),
    spawn=SpawnProfile(1.6, 0.5, 40.0, 100.0, 240.0),
    drain_rate=13.0,
    start_years=380.0,
    par_time=35.0,
)

LEVELS = (LEVEL_ONE, LEVEL_TWO, LEVEL_THREE)


def level_at(index: int) -> LevelDef:
    return LEVELS[max(0, min(index, len(LEVELS) - 1))]


def _supported_platforms(level: LevelDef) -> list[Rect4]:
    return [p for p in level.platforms if p[1] >= INTERNAL_HEIGHT - 40]


def widest_clear_floor(platform: Rect4, hazards: tuple[Rect4, ...]) -> int:
    px, py, pw, _ = platform
    covered: list[tuple[int, int]] = []
    for hx, hy, hw, hh in hazards:
        if hy + hh != py:
            continue
        lo, hi = max(px, hx), min(px + pw, hx + hw)
        if hi > lo:
            covered.append((lo, hi))
    gaps: list[int] = []
    cursor = px
    for lo, hi in sorted(covered):
        if lo > cursor:
            gaps.append(lo - cursor)
        cursor = max(cursor, hi)
    if cursor < px + pw:
        gaps.append(px + pw - cursor)
    return max(gaps) if gaps else pw


def validate_level(level: LevelDef) -> list[str]:
    problems: list[str] = []
    ground_tops = _supported_platforms(level)
    if not ground_tops:
        return [f"{level.name}: no ground platform at the bottom of the screen"]

    for rect in (*level.platforms, *level.obstacles, level.target):
        x, y, w, h = rect
        if x < 0 or y < 0 or x + w > INTERNAL_WIDTH or y + h > INTERNAL_HEIGHT:
            problems.append(
                f"{level.name}: {rect} is outside the {INTERNAL_WIDTH}x{INTERNAL_HEIGHT} screen"
            )

    spawn_x, spawn_y = level.spawn_point
    for rect in level.obstacles:
        rx, ry, rw, rh = rect
        if (
            spawn_x + SPAWN_CLEARANCE > rx
            and spawn_x - SPAWN_CLEARANCE < rx + rw
            and spawn_y < ry + rh + SPAWN_CLEARANCE
            and spawn_y + 16 > ry
        ):
            problems.append(
                f"{level.name}: spawn {level.spawn_point} is too close to obstacle {rect}"
            )

    tx, ty, tw, th = level.target
    for rect in level.obstacles:
        rx, ry, rw, rh = rect
        if tx < rx + rw and tx + tw > rx and ty < ry + rh and ty + th > ry:
            problems.append(f"{level.name}: target {level.target} overlaps obstacle {rect}")

    for mover in level.movers:
        if mover.x_max <= mover.x_min:
            problems.append(f"{level.name}: mover {mover.rect} has an empty patrol range")
        if mover.rect[0] < mover.x_min or mover.rect[0] + mover.rect[2] > mover.x_max:
            problems.append(
                f"{level.name}: mover {mover.rect} does not fit inside its patrol range"
            )

    supported = [p for p in level.platforms if abs(p[1] - (ty + th)) <= 1]
    if not supported:
        problems.append(f"{level.name}: target {level.target} is not resting on any platform")

    reachable = list(ground_tops)
    pending = sorted(
        (p for p in level.platforms if p not in ground_tops),
        key=lambda p: -p[1],
    )
    for rect in pending:
        x, y, w, h = rect
        reachable_from = [
            (bx, by, bw)
            for bx, by, bw, _ in reachable
            if by - y <= RISE_BUDGET and max(bx - (x + w), x - (bx + bw), 0) <= REACH_BUDGET
        ]
        if not reachable_from:
            problems.append(
                f"{level.name}: platform {rect} is unreachable "
                f"(rise budget {RISE_BUDGET:.1f}px, reach budget {REACH_BUDGET:.1f}px)"
            )
        else:
            reachable.append(rect)

    for rect in level.platforms:
        gap = widest_clear_floor(rect, level.hazards)
        if gap < PLAYER_WIDTH:
            problems.append(
                f"{level.name}: platform {rect} leaves {gap}px of clear floor, "
                f"but the player is {PLAYER_WIDTH}px wide and cannot stand there"
            )

    return problems


def validate_all() -> list[str]:
    problems: list[str] = []
    for level in LEVELS:
        problems.extend(validate_level(level))
    for earlier, later in zip(LEVELS, LEVELS[1:], strict=False):
        if later.drain_rate < earlier.drain_rate:
            problems.append(
                f"difficulty regression: {later.name} drains slower than {earlier.name}"
            )
        if later.spawn.ramp_seconds > earlier.spawn.ramp_seconds:
            problems.append(f"difficulty regression: {later.name} ramps slower than {earlier.name}")
    return problems
