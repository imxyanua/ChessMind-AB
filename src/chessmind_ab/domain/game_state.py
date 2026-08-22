"""Full game snapshot at one ply."""

from __future__ import annotations

from dataclasses import dataclass

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


class InvalidGameStateError(ValueError):
    """Raised when a GameState violates core invariants."""


@dataclass(slots=True)
class GameState:
    board: Board
    side_to_move: Color
    status: GameStatus
    ply_count: int

    def __post_init__(self) -> None:
        if self.ply_count < 0:
            raise InvalidGameStateError("ply_count must be >= 0")
        if self.side_to_move is None:
            raise InvalidGameStateError("side_to_move is required")
        if self.status is None:
            raise InvalidGameStateError("status is required")

    def copy(self) -> GameState:
        return GameState(
            board=self.board.copy(),
            side_to_move=self.side_to_move,
            status=self.status,
            ply_count=self.ply_count,
        )

    def count_kings(self, color: Color) -> int:
        count = 0
        for row in range(8):
            for column in range(8):
                piece = self.board.get_piece(Position(row=row, column=column))
                if (
                    piece is not None
                    and piece.type is PieceType.KING
                    and piece.color is color
                ):
                    count += 1
        return count

    def validate_king_invariant(self) -> None:
        white_kings = self.count_kings(Color.WHITE)
        black_kings = self.count_kings(Color.BLACK)
        if white_kings != 1 or black_kings != 1:
            raise InvalidGameStateError(
                "Expected 1 white and 1 black king, "
                f"got white={white_kings}, black={black_kings}"
            )
