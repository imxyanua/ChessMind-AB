"""Alpha-Beta search equivalent to Minimax with pruning."""

from __future__ import annotations

import random
import time

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.debug_log import log_search, move_label
from chessmind_ab.search.evaluation import EvaluationFunction
from chessmind_ab.search.move_ordering import MoveOrdering
from chessmind_ab.search.quiescence import quiescence
from chessmind_ab.search.search_result import SearchResult
from chessmind_ab.search.search_statistics import SearchStatistics
from chessmind_ab.search.terminal import terminal_score


class AlphaBetaSearch:
    def __init__(
        self,
        evaluation: EvaluationFunction | None = None,
        move_ordering: MoveOrdering | None = None,
        diversity_window: int = 0,
        rng: random.Random | None = None,
    ) -> None:
        self._evaluation = evaluation or EvaluationFunction()
        self._move_ordering = move_ordering
        self._diversity_window = max(0, diversity_window)
        self._rng = rng

    def find_best_move(
        self,
        state: GameState,
        depth: int,
        diversity_window: int | None = None,
    ) -> SearchResult:
        if depth < 1:
            raise ValueError("depth must be >= 1")

        window = (
            self._diversity_window if diversity_window is None else max(0, diversity_window)
        )

        stats = SearchStatistics()
        started = time.perf_counter()
        status = GameStatusEvaluator.evaluate(state)
        if status is not GameStatus.ONGOING:
            stats.terminal_nodes += 1
            stats.nodes_visited += 1
            stats.execution_time_ms = (time.perf_counter() - started) * 1000
            return SearchResult(
                best_move=None,
                best_score=terminal_score(status, distance_from_root=0),
                statistics=stats,
            )

        moves = LegalMoveGenerator.generate(state)
        if self._move_ordering is not None:
            moves = self._move_ordering.order(state, moves)
        stats.generated_moves += len(moves)

        scored_moves: list[tuple[Move, int]] = []
        alpha = float("-inf")
        beta = float("inf")
        best_score = float("-inf") if state.side_to_move is Color.WHITE else float("inf")

        for move in moves:
            child = StateTransition.apply(state, move)
            score = self._search(child, depth - 1, 1, alpha, beta, stats)
            scored_moves.append((move, score))
            log_search(
                depth=depth,
                move=move_label(move),
                alpha=alpha,
                beta=beta,
                score=score,
                cutoff=False,
            )
            if state.side_to_move is Color.WHITE:
                if score > best_score:
                    best_score = score
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                beta = min(beta, best_score)

        best_move = self._pick_root_move(
            state.side_to_move, scored_moves, int(best_score), window
        )
        stats.max_depth_reached = depth
        stats.execution_time_ms = (time.perf_counter() - started) * 1000
        return SearchResult(
            best_move=best_move,
            best_score=int(best_score),
            statistics=stats,
        )

    def _pick_root_move(
        self,
        side: Color,
        scored_moves: list[tuple[Move, int]],
        best_score: int,
        diversity_window: int,
    ) -> Move | None:
        if not scored_moves:
            return None

        if diversity_window <= 0 or self._rng is None:
            # Deterministic tie-break: first move that achieved best_score.
            for move, score in scored_moves:
                if score == best_score:
                    return move
            return scored_moves[0][0]

        if side is Color.WHITE:
            candidates = [
                move
                for move, score in scored_moves
                if score >= best_score - diversity_window
            ]
        else:
            candidates = [
                move
                for move, score in scored_moves
                if score <= best_score + diversity_window
            ]
        if not candidates:
            candidates = [move for move, score in scored_moves if score == best_score]
        return self._rng.choice(candidates)

    def _search(
        self,
        state: GameState,
        depth: int,
        distance_from_root: int,
        alpha: float,
        beta: float,
        stats: SearchStatistics,
    ) -> int:
        stats.nodes_visited += 1
        status = GameStatusEvaluator.evaluate(state)
        if status is not GameStatus.ONGOING:
            stats.terminal_nodes += 1
            return terminal_score(status, distance_from_root)

        if depth == 0:
            return quiescence(
                state,
                alpha,
                beta,
                distance_from_root,
                self._evaluation,
                stats,
                self._move_ordering,
            )

        moves = LegalMoveGenerator.generate(state)
        if self._move_ordering is not None:
            moves = self._move_ordering.order(state, moves)
        stats.generated_moves += len(moves)

        if state.side_to_move is Color.WHITE:
            best = float("-inf")
            for index, move in enumerate(moves):
                child = StateTransition.apply(state, move)
                score = self._search(
                    child, depth - 1, distance_from_root + 1, alpha, beta, stats
                )
                best = max(best, score)
                alpha = max(alpha, best)
                if alpha >= beta:
                    cutoff = index < len(moves) - 1
                    if cutoff:
                        stats.cutoffs += 1
                    log_search(
                        depth=depth,
                        move=move_label(move),
                        alpha=alpha,
                        beta=beta,
                        score=score,
                        cutoff=cutoff,
                    )
                    break
            return int(best)

        best = float("inf")
        for index, move in enumerate(moves):
            child = StateTransition.apply(state, move)
            score = self._search(
                child, depth - 1, distance_from_root + 1, alpha, beta, stats
            )
            best = min(best, score)
            beta = min(beta, best)
            if alpha >= beta:
                cutoff = index < len(moves) - 1
                if cutoff:
                    stats.cutoffs += 1
                log_search(
                    depth=depth,
                    move=move_label(move),
                    alpha=alpha,
                    beta=beta,
                    score=score,
                    cutoff=cutoff,
                )
                break
        return int(best)
