"""Game status values for a position snapshot."""

from enum import Enum, auto


class GameStatus(Enum):
    ONGOING = auto()
    WHITE_WINS_CHECKMATE = auto()
    BLACK_WINS_CHECKMATE = auto()
    STALEMATE = auto()
    DRAW = auto()
