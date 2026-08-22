"""Material evaluation for non-terminal positions."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position

MATERIAL_VALUES = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
}


class EvaluationFunction:
    @staticmethod
    def evaluate(state: GameState) -> int:
        score = 0
        for row in range(8):
            for column in range(8):
                piece = state.board.get_piece(Position(row=row, column=column))
                if piece is None or piece.type is PieceType.KING:
                    continue
                value = MATERIAL_VALUES[piece.type]
                score += value if piece.color is Color.WHITE else -value
        return score
