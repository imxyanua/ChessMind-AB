"""Quiescence search: continue through captures/promotions before evaluating."""

from __future__ import annotations

from chessmind_ab.domain.attack_detector import AttackDetector
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

# En passant is a capture onto an empty square; it must be searched at the
# horizon the same way a normal capture is.
_TACTICAL_TYPES = {
    MoveType.CAPTURE,
    MoveType.PROMOTION,
    MoveType.PROMOTION_CAPTURE,
    MoveType.EN_PASSANT,
}


def _order_moves(
    state: GameState, moves: list[Move], move_ordering: MoveOrdering | None
) -> list[Move]:
    if move_ordering is not None:
        return move_ordering.order(state, moves)
    return moves


def tactical_moves(
    state: GameState, move_ordering: MoveOrdering | None = None
) -> list[Move]:
    moves = [
        move
        for move in LegalMoveGenerator.generate(state)
        if move.move_type in _TACTICAL_TYPES
    ]
    return _order_moves(state, moves, move_ordering)


def _play_moves(
    state: GameState,
    moves: list[Move],
    alpha: float,
    beta: float,
    distance_from_root: int,
    evaluation: EvaluationFunction,
    stats: SearchStatistics,
    move_ordering: MoveOrdering | None,
    *,
    is_white: bool,
    best: float,
) -> int:
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
        if is_white:
            best = max(best, score)
            alpha = max(alpha, best)
        else:
            best = min(best, score)
            beta = min(beta, best)
        if alpha >= beta:
            if index < len(moves) - 1:
                stats.cutoffs += 1
            break
    return int(best)


def quiescence(
    state: GameState,
    alpha: float,
    beta: float,
    distance_from_root: int,
    evaluation: EvaluationFunction,
    stats: SearchStatistics,
    move_ordering: MoveOrdering | None = None,
) -> int:
    """Fail-soft quiescence under WHITE=MAX / BLACK=MIN.

    Standing pat is only legal when the side to move is not in check.
    In check, every legal evasion is searched (not just captures).
    """
    stats.nodes_visited += 1

    status = GameStatusEvaluator.evaluate(state)
    if status is not GameStatus.ONGOING:
        stats.terminal_nodes += 1
        return terminal_score(status, distance_from_root)

    is_white = state.side_to_move is Color.WHITE
    in_check = AttackDetector.is_king_in_check(state, state.side_to_move)
    if in_check:
        moves = _order_moves(
            state, LegalMoveGenerator.generate(state), move_ordering
        )
        stats.generated_moves += len(moves)
        if not moves:
            return terminal_score(GameStatusEvaluator.evaluate(state), distance_from_root)
        return _play_moves(
            state,
            moves,
            alpha,
            beta,
            distance_from_root,
            evaluation,
            stats,
            move_ordering,
            is_white=is_white,
            best=float("-inf") if is_white else float("inf"),
        )

    stand_pat = evaluation.evaluate(state)
    stats.evaluated_leaf_nodes += 1

    if is_white:
        if stand_pat >= beta:
            return stand_pat
        best = stand_pat
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return stand_pat
        best = stand_pat
        beta = min(beta, stand_pat)

    moves = tactical_moves(state, move_ordering)
    stats.generated_moves += len(moves)
    return _play_moves(
        state,
        moves,
        alpha,
        beta,
        distance_from_root,
        evaluation,
        stats,
        move_ordering,
        is_white=is_white,
        best=best,
    )
