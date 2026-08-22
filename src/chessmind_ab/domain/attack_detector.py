"""Detect attacked squares from piece attack patterns (not legal moves)."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position

_KNIGHT_DELTAS = (
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
)
_KING_DELTAS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)
_BISHOP_DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_ROOK_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _in_bounds(row: int, column: int) -> bool:
    return 0 <= row < 8 and 0 <= column < 8


class AttackDetector:
    @staticmethod
    def is_square_attacked(
        state: GameState, square: Position, attacker: Color
    ) -> bool:
        for row in range(8):
            for column in range(8):
                origin = Position(row=row, column=column)
                piece = state.board.get_piece(origin)
                if piece is None or piece.color is not attacker:
                    continue
                if AttackDetector._piece_attacks(state, origin, piece, square):
                    return True
        return False

    @staticmethod
    def is_king_in_check(state: GameState, king_color: Color) -> bool:
        king_square = state.board.find_king(king_color)
        return AttackDetector.is_square_attacked(
            state, king_square, king_color.opposite()
        )

    @staticmethod
    def _piece_attacks(
        state: GameState, origin: Position, piece: Piece, target: Position
    ) -> bool:
        if piece.type is PieceType.PAWN:
            direction = -1 if piece.color is Color.WHITE else 1
            return target.row == origin.row + direction and abs(
                target.column - origin.column
            ) == 1
        if piece.type is PieceType.KNIGHT:
            return (target.row - origin.row, target.column - origin.column) in _KNIGHT_DELTAS
        if piece.type is PieceType.KING:
            return (target.row - origin.row, target.column - origin.column) in _KING_DELTAS
        if piece.type is PieceType.BISHOP:
            return AttackDetector._ray_attacks(state, origin, target, _BISHOP_DIRS)
        if piece.type is PieceType.ROOK:
            return AttackDetector._ray_attacks(state, origin, target, _ROOK_DIRS)
        if piece.type is PieceType.QUEEN:
            return AttackDetector._ray_attacks(
                state, origin, target, _BISHOP_DIRS + _ROOK_DIRS
            )
        return False

    @staticmethod
    def _ray_attacks(
        state: GameState,
        origin: Position,
        target: Position,
        directions: tuple[tuple[int, int], ...],
    ) -> bool:
        dr = target.row - origin.row
        dc = target.column - origin.column
        if dr == 0 and dc == 0:
            return False
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        if (step_r, step_c) not in directions:
            return False
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False

        row = origin.row + step_r
        column = origin.column + step_c
        while _in_bounds(row, column):
            current = Position(row=row, column=column)
            if current == target:
                return True
            if state.board.get_piece(current) is not None:
                return False
            row += step_r
            column += step_c
        return False
