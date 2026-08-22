"""Quiescence search: continue through captures/promotions before evaluating."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.evaluation import EvaluationFunction
from chessmind_ab.search.move_ordering import MoveOrdering
from chessmind_ab.search.search_statistics import SearchStatistics
from chessmind_ab.search.terminal import terminal_score

_TACTICAL_TYPES = {
    MoveType.CAPTURE,
    MoveType.PROMOTION,
    MoveType.PROMOTION_CAPTURE,
}


def tactical_moves(
    state: GameState, move_ordering: MoveOrdering | None = None
) -> list[Move]:
    moves = [
        move
        for move in LegalMoveGenerator.generate(state)
        if move.move_type in _TACTICAL_TYPES
    ]
    if move_ordering is not None:
        moves = move_ordering.order(state, moves)
    return moves


def quiescence(
    state: GameState,
    alpha: float,
    beta: float,
    distance_from_root: int,
    evaluation: EvaluationFunction,
    stats: SearchStatistics,
    move_ordering: MoveOrdering | None = None,
) -> int:
    """Fail-soft quiescence under WHITE=MAX / BLACK=MIN."""
    stats.nodes_visited += 1

    status = GameStatusEvaluator.evaluate(state)
    if status is not GameStatus.ONGOING:
        stats.terminal_nodes += 1
        return terminal_score(status, distance_from_root)

    stand_pat = evaluation.evaluate(state)
    stats.evaluated_leaf_nodes += 1

    if state.side_to_move is Color.WHITE:
        if stand_pat >= beta:
            return stand_pat
        best = stand_pat
        alpha = max(alpha, stand_pat)
        moves = tactical_moves(state, move_ordering)
        stats.generated_moves += len(moves)
        for index, move in enumerate(moves):
            child = StateTransition.apply(state, move)
            score = quiescence(
                child,
                alpha,
                beta,
                distance_from_root + 1,
                evaluation,
                stats,
                move_ordering,
            )
            best = max(best, score)
            alpha = max(alpha, best)
            if alpha >= beta:
                if index < len(moves) - 1:
                    stats.cutoffs += 1
                break
        return int(best)

    if stand_pat <= alpha:
        return stand_pat
    best = stand_pat
    beta = min(beta, stand_pat)
    moves = tactical_moves(state, move_ordering)
    stats.generated_moves += len(moves)
    for index, move in enumerate(moves):
        child = StateTransition.apply(state, move)
        score = quiescence(
            child,
            alpha,
            beta,
            distance_from_root + 1,
            evaluation,
            stats,
            move_ordering,
        )
        best = min(best, score)
        beta = min(beta, best)
        if alpha >= beta:
            if index < len(moves) - 1:
                stats.cutoffs += 1
            break
    return int(best)
