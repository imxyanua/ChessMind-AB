"""Generate legal moves by filtering pseudo moves for king safety."""

from __future__ import annotations

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator
from chessmind_ab.domain.state_transition import StateTransition


class LegalMoveGenerator:
    @staticmethod
    def generate(state: GameState) -> list[Move]:
        side = state.side_to_move
        legal: list[Move] = []
        for move in PseudoMoveGenerator.generate(state, side):
            if move.move_type in {
                MoveType.CASTLING_KING_SIDE,
                MoveType.CASTLING_QUEEN_SIDE,
            }:
                if not LegalMoveGenerator._castling_is_legal(state, move):
                    continue
            child = StateTransition.apply(state, move)
            if not AttackDetector.is_king_in_check(child, side):
                legal.append(move)
        return legal

    @staticmethod
    def _castling_is_legal(state: GameState, move: Move) -> bool:
        side = state.side_to_move
        if AttackDetector.is_king_in_check(state, side):
            return False
        row = move.from_position.row
        if move.move_type is MoveType.CASTLING_KING_SIDE:
            path = (4, 5, 6)
        else:
            path = (4, 3, 2)
        for column in path:
            square = Position(row=row, column=column)
            if AttackDetector.is_square_attacked(state, square, side.opposite()):
                return False
        return True
