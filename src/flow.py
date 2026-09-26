from src.chamber import Chamber
from src.levels import LEVELS, level_at
from src.progression import Progress
from src.session import Session


class Flow:
    def __init__(self, progress: Progress | None = None) -> None:
        self.progress = progress if progress is not None else Progress()
        self.level_index = 0
        self.chamber: Chamber = Chamber(level_at(0))
        self.session: Session = Session(self.chamber)

    @property
    def level_count(self) -> int:
        return len(LEVELS)

    def start(self, index: int) -> None:
        self.level_index = max(0, min(index, self.level_count - 1))
        self.chamber = Chamber(level_at(self.level_index))
        self.session = Session(self.chamber)

    def restart(self) -> None:
        self.start(self.level_index)

    def advance(self) -> bool:
        if self.level_index + 1 < self.level_count:
            self.start(self.level_index + 1)
            return True
        return False

    def record_win(self) -> None:
        self.progress.record_clear(
            self.level_index, self.session.elapsed, self.session.earth_alloc
        )
