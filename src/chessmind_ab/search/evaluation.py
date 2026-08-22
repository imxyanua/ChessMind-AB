"""Evaluation V2: material + piece-square tables."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator

MATERIAL_VALUES = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
}

# Tables are from White's perspective (row 0 = rank 8). Black uses vertically mirrored values.
_PAWN_PST = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

_KNIGHT_PST = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

_BISHOP_PST = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

_ROOK_PST = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]

_QUEEN_PST = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]

_KING_PST = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]

_PST_BY_TYPE = {
    PieceType.PAWN: _PAWN_PST,
    PieceType.KNIGHT: _KNIGHT_PST,
    PieceType.BISHOP: _BISHOP_PST,
    PieceType.ROOK: _ROOK_PST,
    PieceType.QUEEN: _QUEEN_PST,
    PieceType.KING: _KING_PST,
}


def _pst_value(piece_type: PieceType, color: Color, row: int, column: int) -> int:
    table = _PST_BY_TYPE[piece_type]
    if color is Color.WHITE:
        return table[row][column]
    return table[7 - row][column]


# Small weight so mobility nudges style without overpowering material/PST.
_MOBILITY_WEIGHT = 4


class EvaluationFunction:
    @staticmethod
    def evaluate(state: GameState) -> int:
        score = 0
        for row in range(8):
            for column in range(8):
                piece = state.board.get_piece(Position(row=row, column=column))
                if piece is None:
                    continue
                # King has no material value; use == (not `is`) for enum safety.
                material = 0 if piece.type == PieceType.KING else MATERIAL_VALUES.get(
                    piece.type, 0
                )
                pst = _pst_value(piece.type, piece.color, row, column)
                term = material + pst
                score += term if piece.color == Color.WHITE else -term

        white_mobility = len(PseudoMoveGenerator.generate(state, Color.WHITE))
        black_mobility = len(PseudoMoveGenerator.generate(state, Color.BLACK))
        score += _MOBILITY_WEIGHT * (white_mobility - black_mobility)
        return score
