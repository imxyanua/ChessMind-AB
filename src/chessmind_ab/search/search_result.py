"""Result of a search call."""

from __future__ import annotations

from dataclasses import dataclass

from chessmind_ab.domain.move import Move
from chessmind_ab.search.search_statistics import SearchStatistics


@dataclass(slots=True)
class SearchResult:
    best_move: Move | None
    best_score: int
    statistics: SearchStatistics
