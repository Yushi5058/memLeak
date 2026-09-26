from src.achievements import earned_on_clear
from src.chamber import Chamber
from src.chapters import chapter_for
from src.levels import LEVELS, level_at
from src.progression import Progress
from src.prologue import Prologue
from src.session import Session


class Flow:
    def __init__(self, progress: Progress | None = None) -> None:
        self.progress = progress if progress is not None else Progress()
        self.level_index = 0
        self.chamber: Chamber = Chamber(level_at(0))
        self.session: Session = Session(self.chamber)
        self.unlocked_awards: list[str] = []

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

    def pending_chapter(self) -> Prologue | None:
        """The chapter introducing the current chamber, if it has not been seen.

        Returns None for the first chamber, which the prologue introduces, and
        for any chapter already watched.
        """
        if not 1 <= self.level_index < self.level_count:
            return None
        if self.progress.has_seen_chapter(self.level_index):
            return None
        return chapter_for(self.level_index)

    def mark_chapter_seen(self) -> bool:
        return self.progress.mark_chapter_seen(self.level_index)

    def record_win(self) -> None:
        session = self.session
        level = self.chamber.level
        already_cleared = self.progress.has_cleared(self.level_index)
        self.progress.record_clear(
            self.level_index, session.elapsed, session.earth_alloc
        )
        for key in earned_on_clear(
            level,
            session.elapsed,
            session.earth_alloc,
            session.hits,
            already_cleared,
            len(self.progress.cleared),
        ):
            if self.progress.unlock_achievement(key):
                self.unlocked_awards.append(key)
