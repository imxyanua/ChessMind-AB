"""Move classification for core rules."""

from enum import Enum, auto


class MoveType(Enum):
    NORMAL = auto()
    CAPTURE = auto()
    PAWN_DOUBLE = auto()
    PROMOTION = auto()
    PROMOTION_CAPTURE = auto()
    EN_PASSANT = auto()
    CASTLING_KING_SIDE = auto()
    CASTLING_QUEEN_SIDE = auto()
