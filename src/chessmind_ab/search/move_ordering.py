"""Deterministic move ordering: promotion, MVV-LVA captures, checks, then quiet."""

from __future__ import annotations

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.evaluation import MATERIAL_VALUES

_ATTACKER_VALUES = {
    **MATERIAL_VALUES,
    PieceType.KING: 50,
}


class MoveOrdering:
    @staticmethod
    def order(state: GameState, moves: list[Move]) -> list[Move]:
        scored: list[tuple[tuple[int, int], int, Move]] = []
        for index, move in enumerate(moves):
            scored.append((MoveOrdering._priority(state, move), index, move))
        scored.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in scored]

    @staticmethod
    def _priority(state: GameState, move: Move) -> tuple[int, int]:
        if move.move_type in {MoveType.PROMOTION, MoveType.PROMOTION_CAPTURE}:
            # Prefer stronger promotion piece first among promotions.
            promo = MATERIAL_VALUES.get(move.promotion_piece or PieceType.QUEEN, 0)
            capture_bonus = 0
            if move.captured_piece is not None:
                capture_bonus = MATERIAL_VALUES.get(move.captured_piece.type, 0)
            return (0, -(promo + capture_bonus))

        if move.move_type is MoveType.CAPTURE:
            if move.captured_piece is None:
                return (1, 0)
            victim = MATERIAL_VALUES.get(move.captured_piece.type, 0)
            attacker = _ATTACKER_VALUES.get(move.moving_piece.type, 0)
            return (1, -(victim * 10 - attacker))

        if MoveOrdering._gives_check(state, move):
            return (2, 0)

        return (3, 0)

    @staticmethod
    def _gives_check(state: GameState, move: Move) -> bool:
        child = StateTransition.apply(state, move)
        # After apply, side_to_move is the opponent who must answer the check.
        return AttackDetector.is_king_in_check(child, child.side_to_move)
