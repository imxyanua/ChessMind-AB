"""Tests for iterative deepening with a soft time budget."""

import time

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.iterative_deepening import iterative_deepening_search
from chessmind_ab.search.move_ordering import MoveOrdering


def _tiny() -> GameState:
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    board.set_piece(
        Position.from_chess_notation("d1"),
        Piece(type=PieceType.QUEEN, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("d8"),
        Piece(type=PieceType.QUEEN, color=Color.BLACK),
    )
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_iterative_deepening_returns_move_and_tracks_depth() -> None:
    search = AlphaBetaSearch(move_ordering=MoveOrdering())
    result = iterative_deepening_search(
        search,
        _tiny(),
        time_budget_ms=2000,
        max_depth=2,
    )
    assert result.best_move is not None
    assert result.statistics.max_depth_reached >= 1
    assert result.statistics.max_depth_reached <= 2
    assert result.statistics.nodes_visited > 0


def test_fixed_depth_search_still_available_for_benchmarks() -> None:
    search = AlphaBetaSearch(move_ordering=MoveOrdering())
    fixed = search.find_best_move(_tiny(), 1)
    timed = iterative_deepening_search(
        search,
        _tiny(),
        time_budget_ms=500,
        max_depth=1,
    )
    assert fixed.best_score == timed.best_score
    assert fixed.statistics.max_depth_reached == 1


def test_id_aborts_near_budget_instead_of_waiting_out_max_depth() -> None:
    search = AlphaBetaSearch(move_ordering=MoveOrdering())
    started = time.perf_counter()
    result = iterative_deepening_search(
        search,
        create_initial_game_state(),
        time_budget_ms=80,
        max_depth=6,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert result.best_move is not None
    assert elapsed_ms < 700
    assert result.statistics.max_depth_reached <= 3
    assert search.was_stopped() is False
