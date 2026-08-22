"""Generate legal moves by filtering pseudo moves for king safety."""

from __future__ import annotations

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator
from chessmind_ab.domain.state_transition import StateTransition


class LegalMoveGenerator:
    @staticmethod
    def generate(state: GameState) -> list[Move]:
        side = state.side_to_move
        legal: list[Move] = []
        for move in PseudoMoveGenerator.generate(state, side):
            child = StateTransition.apply(state, move)
            if not AttackDetector.is_king_in_check(child, side):
                legal.append(move)
        return legal
