"""Minimax search with WHITE=MAX and BLACK=MIN."""

from __future__ import annotations

import time

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.evaluation import EvaluationFunction
from chessmind_ab.search.quiescence import quiescence
from chessmind_ab.search.search_result import SearchResult
from chessmind_ab.search.search_statistics import SearchStatistics
from chessmind_ab.search.terminal import terminal_score


class MinimaxSearch:
    def __init__(
        self,
        evaluation: EvaluationFunction | None = None,
        *,
        use_quiescence: bool = True,
    ) -> None:
        self._evaluation = evaluation or EvaluationFunction()
        self._use_quiescence = use_quiescence
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def reset_cancel(self) -> None:
        self._cancelled = False

    def find_best_move(self, state: GameState, depth: int) -> SearchResult:
        if depth < 1:
            raise ValueError("depth must be >= 1")

        stats = SearchStatistics()
        started = time.perf_counter()
        status, moves = GameStatusEvaluator.evaluate_with_moves(state)
        if status is not GameStatus.ONGOING:
            stats.terminal_nodes += 1
            stats.nodes_visited += 1
            stats.execution_time_ms = (time.perf_counter() - started) * 1000
            return SearchResult(
                best_move=None,
                best_score=terminal_score(status, distance_from_root=0),
                statistics=stats,
            )

        stats.generated_moves += len(moves)
        best_move: Move | None = None
        best_score = float("-inf") if state.side_to_move is Color.WHITE else float("inf")

        for move in moves:
            if self._cancelled:
                break
            child = StateTransition.apply(state, move)
            score = self._search(child, depth - 1, 1, stats)
            if state.side_to_move is Color.WHITE:
                if score > best_score:
                    best_score = score
                    best_move = move
            elif score < best_score:
                best_score = score
                best_move = move

        stats.max_depth_reached = depth
        stats.execution_time_ms = (time.perf_counter() - started) * 1000
        if best_move is None and moves:
            best_move = moves[0]
            best_score = 0
        return SearchResult(
            best_move=best_move,
            best_score=int(best_score) if best_score not in {float("-inf"), float("inf")} else 0,
            statistics=stats,
        )

    def _search(
        self,
        state: GameState,
        depth: int,
        distance_from_root: int,
        stats: SearchStatistics,
    ) -> int:
        stats.nodes_visited += 1
        if self._cancelled:
            return 0
        status, moves = GameStatusEvaluator.evaluate_with_moves(state)
        if status is not GameStatus.ONGOING:
            stats.terminal_nodes += 1
            return terminal_score(status, distance_from_root)

        if depth == 0:
            if self._use_quiescence:
                return quiescence(
                    state,
                    float("-inf"),
                    float("inf"),
                    distance_from_root,
                    self._evaluation,
                    stats,
                    move_ordering=None,
                    legal_moves=moves,
                )
            stats.evaluated_leaf_nodes += 1
            return self._evaluation.evaluate(state)

        stats.generated_moves += len(moves)
        if state.side_to_move is Color.WHITE:
            best = float("-inf")
            for move in moves:
                if self._cancelled:
                    break
                child = StateTransition.apply(state, move)
                best = max(
                    best,
                    self._search(child, depth - 1, distance_from_root + 1, stats),
                )
            return int(best) if best != float("-inf") else 0

        best = float("inf")
        for move in moves:
            if self._cancelled:
                break
            child = StateTransition.apply(state, move)
            best = min(
                best,
                self._search(child, depth - 1, distance_from_root + 1, stats),
            )
        return int(best) if best != float("inf") else 0
