"""8x8 board storage with deep copy and king lookup."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import InvalidPositionError, Position


class KingNotFoundError(ValueError):
    """Raised when a king of the requested color is missing."""


class Board:
    def __init__(self) -> None:
        self._squares: list[list[Piece | None]] = [
            [None for _ in range(8)] for _ in range(8)
        ]

    def get_piece(self, position: Position) -> Piece | None:
        return self._squares[position.row][position.column]

    def set_piece(self, position: Position, piece: Piece) -> None:
        self._squares[position.row][position.column] = piece

    def remove_piece(self, position: Position) -> Piece | None:
        piece = self._squares[position.row][position.column]
        self._squares[position.row][position.column] = None
        return piece

    def copy(self) -> Board:
        cloned = Board()
        for row in range(8):
            for column in range(8):
                piece = self._squares[row][column]
                if piece is not None:
                    cloned._squares[row][column] = Piece(
                        type=piece.type,
                        color=piece.color,
                    )
        return cloned

    def find_king(self, color: Color) -> Position:
        for row in range(8):
            for column in range(8):
                piece = self._squares[row][column]
                if (
                    piece is not None
                    and piece.type is PieceType.KING
                    and piece.color is color
                ):
                    return Position(row=row, column=column)
        raise KingNotFoundError(f"King not found for color {color.name}")

    def __getitem__(self, position: Position) -> Piece | None:
        if not isinstance(position, Position):
            raise InvalidPositionError("Board index must be a Position")
        return self.get_piece(position)
