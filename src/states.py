from enum import Enum, auto


class State(Enum):
    TITLE = auto()
    PROLOGUE = auto()
    PLAY = auto()
    PAUSED = auto()
    CLEARED = auto()
    GAMEOVER = auto()
