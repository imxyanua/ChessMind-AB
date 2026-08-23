"""Chess move value object with core invariants."""

from __future__ import annotations

from dataclasses import dataclass

from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position

_PROMOTION_TYPES = {
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT,
}

_PROMOTION_MOVE_TYPES = {MoveType.PROMOTION, MoveType.PROMOTION_CAPTURE}
_CAPTURE_MOVE_TYPES = {
    MoveType.CAPTURE,
    MoveType.PROMOTION_CAPTURE,
    MoveType.EN_PASSANT,
}


class InvalidMoveError(ValueError):
    """Raised when a Move violates core invariants."""


@dataclass(frozen=True, slots=True)
class Move:
    from_position: Position
    to_position: Position
    moving_piece: Piece
    move_type: MoveType
    captured_piece: Piece | None = None
    promotion_piece: PieceType | None = None

    def __post_init__(self) -> None:
        if self.from_position == self.to_position:
            raise InvalidMoveError("from_position and to_position must differ")

        if self.move_type in _PROMOTION_MOVE_TYPES:
            if self.promotion_piece is None:
                raise InvalidMoveError("Promotion moves require promotion_piece")
            if self.promotion_piece not in _PROMOTION_TYPES:
                raise InvalidMoveError(
                    f"Invalid promotion piece: {self.promotion_piece}"
                )
        elif self.promotion_piece is not None:
            raise InvalidMoveError(
                "promotion_piece is only allowed for promotion move types"
            )

        if self.move_type in _CAPTURE_MOVE_TYPES:
            if self.captured_piece is None:
                raise InvalidMoveError("Capture moves require captured_piece")
        elif self.captured_piece is not None:
            raise InvalidMoveError(
                "captured_piece is only allowed for capture move types"
            )

        if self.move_type in {
            MoveType.CASTLING_KING_SIDE,
            MoveType.CASTLING_QUEEN_SIDE,
        }:
            if self.moving_piece.type is not PieceType.KING:
                raise InvalidMoveError("Castling moves require the king")
