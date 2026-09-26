import json
from pathlib import Path

from src.levels import LEVELS

SAVE_VERSION = 1
DEFAULT_PATH = Path.home() / ".memleak" / "progress.json"


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_keyed_floats(raw) -> dict[int, float]:
    if not isinstance(raw, dict):
        return {}
    parsed: dict[int, float] = {}
    for key, value in raw.items():
        index = _as_int(key, -1)
        number = _as_float(value)
        if index >= 0 and number is not None:
            parsed[index] = number
    return parsed


class Progress:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_PATH
        self.unlocked = 1
        self.cleared: list[int] = []
        self.best_time: dict[int, float] = {}
        self.best_years: dict[int, float] = {}
        self.achievements: list[str] = []
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return
        if not isinstance(raw, dict):
            return
        self.unlocked = max(1, _as_int(raw.get("unlocked", 1), 1))
        cleared = raw.get("cleared", [])
        if isinstance(cleared, list):
            self.cleared = [i for i in (_as_int(v, -1) for v in cleared) if i >= 0]
        else:
            self.cleared = []
        self.best_time = _int_keyed_floats(raw.get("best_time"))
        self.best_years = _int_keyed_floats(raw.get("best_years"))
        achievements = raw.get("achievements", [])
        if isinstance(achievements, list):
            self.achievements = [str(a) for a in achievements]
        else:
            self.achievements = []

    def save(self) -> None:
        payload = {
            "version": SAVE_VERSION,
            "unlocked": self.unlocked,
            "cleared": sorted(set(self.cleared)),
            "best_time": {str(k): v for k, v in self.best_time.items()},
            "best_years": {str(k): v for k, v in self.best_years.items()},
            "achievements": sorted(set(self.achievements)),
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
            tmp.replace(self.path)
        except OSError:
            pass

    def is_unlocked(self, index: int) -> bool:
        return index < self.unlocked

    def has_cleared(self, index: int) -> bool:
        return index in self.cleared

    def record_clear(self, index: int, elapsed: float, years: float) -> None:
        if index not in self.cleared:
            self.cleared.append(index)
        self.unlocked = max(self.unlocked, min(index + 2, len(LEVELS)))
        if index not in self.best_time or elapsed < self.best_time[index]:
            self.best_time[index] = elapsed
        if index not in self.best_years or years > self.best_years[index]:
            self.best_years[index] = years
        self.save()

    def best_for(self, index: int) -> tuple[float, float]:
        return self.best_time.get(index, 0.0), self.best_years.get(index, 0.0)

    def has_achievement(self, name: str) -> bool:
        return name in self.achievements

    def unlock_achievement(self, name: str) -> bool:
        if name in self.achievements:
            return False
        self.achievements.append(name)
        self.save()
        return True
