"""Deterministic move ordering for alpha-beta pruning."""

from __future__ import annotations

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType


class MoveOrdering:
    @staticmethod
    def order(state: GameState, moves: list[Move]) -> list[Move]:
        del state  # ordering V1 is move-type based only

        def priority(move: Move) -> int:
            if move.move_type in {MoveType.PROMOTION, MoveType.PROMOTION_CAPTURE}:
                return 0
            if move.move_type in {MoveType.CAPTURE, MoveType.PROMOTION_CAPTURE}:
                return 1
            return 2

        # Stable sort keeps original relative order for equal priority (tie-break).
        return sorted(moves, key=priority)
