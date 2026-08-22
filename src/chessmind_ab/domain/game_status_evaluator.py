"""Evaluate terminal/non-terminal game status from legal moves."""

from __future__ import annotations

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator


class GameStatusEvaluator:
    @staticmethod
    def evaluate(state: GameState) -> GameStatus:
        legal_moves = LegalMoveGenerator.generate(state)
        if legal_moves:
            return GameStatus.ONGOING

        in_check = AttackDetector.is_king_in_check(state, state.side_to_move)
        if in_check:
            if state.side_to_move is Color.WHITE:
                return GameStatus.BLACK_WINS_CHECKMATE
            return GameStatus.WHITE_WINS_CHECKMATE
        return GameStatus.STALEMATE
