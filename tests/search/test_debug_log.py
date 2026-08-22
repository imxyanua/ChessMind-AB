"""Tests for optional search debug logging."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.debug_log import (
    SearchLogEvent,
    add_sink,
    clear_sinks,
    is_debug_search_enabled,
    set_debug_search,
)
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


def test_debug_logging_disabled_by_default_emits_nothing() -> None:
    events: list[SearchLogEvent] = []
    clear_sinks()
    set_debug_search(False)
    add_sink(events.append)
    AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(_tiny(), 1)
    assert events == []
    clear_sinks()


def test_debug_logging_captures_root_and_optional_cutoffs() -> None:
    events: list[SearchLogEvent] = []
    clear_sinks()
    set_debug_search(True)
    add_sink(events.append)
    try:
        AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(_tiny(), 2)
        assert is_debug_search_enabled()
        assert events
        assert any(event.move for event in events)
        assert any(event.score is not None for event in events)
        assert any(event.alpha is not None for event in events)
    finally:
        set_debug_search(False)
        clear_sinks()
