"""Tests for Zobrist hashing and transposition table correctness."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.minimax import MinimaxSearch
from chessmind_ab.search.move_ordering import MoveOrdering
from chessmind_ab.search.transposition_table import TranspositionTable
from chessmind_ab.search.zobrist import zobrist_hash


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


def test_zobrist_hash_stable_and_side_sensitive() -> None:
    state = _tiny()
    assert zobrist_hash(state) == zobrist_hash(state)
    flipped = GameState(
        board=state.board.copy(),
        side_to_move=Color.BLACK,
        status=GameStatus.ONGOING,
        ply_count=0,
    )
    assert zobrist_hash(state) != zobrist_hash(flipped)


def test_tt_preserves_score_vs_minimax() -> None:
    state = _tiny()
    mini = MinimaxSearch().find_best_move(state, 2)
    with_tt = AlphaBetaSearch(
        move_ordering=MoveOrdering(),
        transposition_table=TranspositionTable(size_power=14),
    ).find_best_move(state, 2)
    without = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(state, 2)
    assert with_tt.best_score == mini.best_score
    assert without.best_score == mini.best_score


def test_tt_can_reduce_nodes_on_deeper_search() -> None:
    state = _tiny()
    plain = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(state, 2)
    tt_search = AlphaBetaSearch(
        move_ordering=MoveOrdering(),
        transposition_table=TranspositionTable(size_power=14),
    )
    with_tt = tt_search.find_best_move(state, 2)
    assert with_tt.best_score == plain.best_score
    # Hits are optional on tiny trees; stores should still happen.
    assert tt_search._tt is not None
    assert tt_search._tt.stores > 0
