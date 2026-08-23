"""Iterative deepening wrapper with a soft time budget."""

from __future__ import annotations

import time

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.search_result import SearchResult
from chessmind_ab.search.search_statistics import SearchStatistics


def iterative_deepening_search(
    search: AlphaBetaSearch,
    state: GameState,
    *,
    time_budget_ms: float,
    max_depth: int,
    diversity_window: int | None = None,
) -> SearchResult:
    """Search depth 1..max_depth, keeping the last completed iteration.

    Time checks happen between iterations (not mid-node) so each finished
    depth stays usable. Benchmarks should keep calling ``find_best_move``
    with a fixed depth for determinism.
    """
    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")
    if time_budget_ms <= 0:
        raise ValueError("time_budget_ms must be > 0")

    deadline = time.perf_counter() + (time_budget_ms / 1000.0)
    started = time.perf_counter()
    best: SearchResult | None = None
    totals = SearchStatistics()

    for depth in range(1, max_depth + 1):
        if best is not None and time.perf_counter() >= deadline:
            break

        result = search.find_best_move(
            state, depth, diversity_window=diversity_window
        )
        totals.nodes_visited += result.statistics.nodes_visited
        totals.evaluated_leaf_nodes += result.statistics.evaluated_leaf_nodes
        totals.terminal_nodes += result.statistics.terminal_nodes
        totals.generated_moves += result.statistics.generated_moves
        totals.cutoffs += result.statistics.cutoffs
        totals.max_depth_reached = depth

        best = SearchResult(
            best_move=result.best_move,
            best_score=result.best_score,
            statistics=SearchStatistics(
                nodes_visited=totals.nodes_visited,
                evaluated_leaf_nodes=totals.evaluated_leaf_nodes,
                terminal_nodes=totals.terminal_nodes,
                generated_moves=totals.generated_moves,
                cutoffs=totals.cutoffs,
                max_depth_reached=totals.max_depth_reached,
                execution_time_ms=0.0,
            ),
        )

        if time.perf_counter() >= deadline:
            break

    if best is None:
        best = search.find_best_move(
            state, 1, diversity_window=diversity_window
        )

    best.statistics.execution_time_ms = (time.perf_counter() - started) * 1000
    return best
