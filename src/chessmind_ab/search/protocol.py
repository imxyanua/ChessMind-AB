"""Shared search algorithm protocol."""

from __future__ import annotations

from typing import Protocol

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.search.search_result import SearchResult


class SearchAlgorithm(Protocol):
    def find_best_move(self, state: GameState, depth: int) -> SearchResult:
        ...
