from pathlib import Path

from src.prologue import Prologue

ROOT = Path(__file__).resolve().parent.parent
TITLE_I = "CHAPTER I"
TITLE_II = "CHAPTER II"
CHAPTER_PATHS = {
    1: ROOT / "CHAPTER_I.txt",
    2: ROOT / "CHAPTER_II.txt",
}
CHAPTER_TITLES = {
    1: TITLE_I,
    2: TITLE_II,
}


def chapter_for(index: int) -> Prologue | None:
    """The script that introduces chamber `index`, or None if it has none.

    The first chamber is introduced by the prologue instead, so it has no
    chapter of its own.
    """
    path = CHAPTER_PATHS.get(index)
    if path is None:
        return None
    return Prologue.from_file(path, title=CHAPTER_TITLES.get(index))


class Narration:
    """Owns whichever script is currently on screen.

    The prologue introduces the first chamber; a chapter introduces any later
    one, and only the first time the player walks into it.
    """

    def __init__(self, prologue: Prologue) -> None:
        self.prologue = prologue
        self.chapter: Prologue | None = None

    @property
    def active(self) -> Prologue:
        return self.prologue if self.chapter is None else self.chapter

    @property
    def in_chapter(self) -> bool:
        return self.chapter is not None

    def begin(self, chapter: Prologue | None) -> None:
        self.chapter = chapter
        self.active.reset()

    def end(self) -> None:
        self.chapter = None
