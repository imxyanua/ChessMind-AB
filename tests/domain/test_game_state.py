"""Unit tests for GameState (P1-5)."""

import pytest

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState, InvalidGameStateError
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def _two_king_board() -> Board:
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    return board


def test_game_state_creation_and_fields() -> None:
    state = GameState(
        board=_two_king_board(),
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )
    assert state.side_to_move is Color.WHITE
    assert state.status is GameStatus.ONGOING
    assert state.ply_count == 0
    state.validate_king_invariant()


def test_negative_ply_count_is_rejected() -> None:
    with pytest.raises(InvalidGameStateError):
        GameState(
            board=_two_king_board(),
            side_to_move=Color.WHITE,
            status=GameStatus.ONGOING,
            ply_count=-1,
        )


def test_king_invariant_helper() -> None:
    state = GameState(
        board=_two_king_board(),
        side_to_move=Color.BLACK,
        status=GameStatus.ONGOING,
        ply_count=3,
    )
    assert state.count_kings(Color.WHITE) == 1
    assert state.count_kings(Color.BLACK) == 1


def test_king_invariant_fails_without_both_kings() -> None:
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    state = GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )
    with pytest.raises(InvalidGameStateError):
        state.validate_king_invariant()


def test_game_state_copy_isolates_board() -> None:
    state = GameState(
        board=_two_king_board(),
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=1,
    )
    cloned = state.copy()
    cloned.board.set_piece(
        Position.from_chess_notation("d4"),
        Piece(type=PieceType.QUEEN, color=Color.WHITE),
    )
    assert state.board.get_piece(Position.from_chess_notation("d4")) is None
    assert cloned.board.get_piece(Position.from_chess_notation("d4")) is not None
