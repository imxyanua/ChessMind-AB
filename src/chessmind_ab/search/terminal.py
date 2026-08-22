"""Shared terminal scoring for search algorithms."""

from __future__ import annotations

from chessmind_ab.domain.game_status import GameStatus

MATE_SCORE = 100_000


def terminal_score(status: GameStatus, distance_from_root: int) -> int:
    if status is GameStatus.WHITE_WINS_CHECKMATE:
        return MATE_SCORE - distance_from_root
    if status is GameStatus.BLACK_WINS_CHECKMATE:
        return -MATE_SCORE + distance_from_root
    return 0
