"""Unit tests for StateTransition Copy-on-Move (P1-6)."""

import pytest

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import (
    IllegalStateTransitionError,
    StateTransition,
)


def _base_state() -> GameState:
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_normal_move_updates_board_side_and_ply() -> None:
    state = _base_state()
    e2 = Position.from_chess_notation("e2")
    e3 = Position.from_chess_notation("e3")
    pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)
    state.board.set_piece(e2, pawn)

    move = Move(
        from_position=e2,
        to_position=e3,
        moving_piece=pawn,
        move_type=MoveType.NORMAL,
    )
    child = StateTransition.apply(state, move)

    assert child.board.get_piece(e2) is None
    assert child.board.get_piece(e3) == pawn
    assert child.side_to_move is Color.BLACK
    assert child.ply_count == 1
    assert state.board.get_piece(e2) == pawn
    assert state.side_to_move is Color.WHITE
    assert state.ply_count == 0


def test_capture_removes_enemy_piece() -> None:
    state = _base_state()
    e4 = Position.from_chess_notation("e4")
    d5 = Position.from_chess_notation("d5")
    white_pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)
    black_knight = Piece(type=PieceType.KNIGHT, color=Color.BLACK)
    state.board.set_piece(e4, white_pawn)
    state.board.set_piece(d5, black_knight)

    move = Move(
        from_position=e4,
        to_position=d5,
        moving_piece=white_pawn,
        move_type=MoveType.CAPTURE,
        captured_piece=black_knight,
    )
    child = StateTransition.apply(state, move)

    assert child.board.get_piece(e4) is None
    assert child.board.get_piece(d5) == white_pawn
    assert state.board.get_piece(d5) == black_knight


def test_promotion_replaces_pawn() -> None:
    state = _base_state()
    e7 = Position.from_chess_notation("e7")
    e8 = Position.from_chess_notation("e8")
    # Move black king away so e8 is free for promotion fixture.
    state.board.remove_piece(e8)
    state.board.set_piece(
        Position.from_chess_notation("a8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    white_pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)
    state.board.set_piece(e7, white_pawn)

    move = Move(
        from_position=e7,
        to_position=e8,
        moving_piece=white_pawn,
        move_type=MoveType.PROMOTION,
        promotion_piece=PieceType.QUEEN,
    )
    child = StateTransition.apply(state, move)

    assert child.board.get_piece(e7) is None
    assert child.board.get_piece(e8) == Piece(
        type=PieceType.QUEEN, color=Color.WHITE
    )


def test_sibling_applies_do_not_affect_each_other() -> None:
    state = _base_state()
    e2 = Position.from_chess_notation("e2")
    d2 = Position.from_chess_notation("d2")
    e3 = Position.from_chess_notation("e3")
    d3 = Position.from_chess_notation("d3")
    e_pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)
    d_pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)
    state.board.set_piece(e2, e_pawn)
    state.board.set_piece(d2, d_pawn)

    child_a = StateTransition.apply(
        state,
        Move(
            from_position=e2,
            to_position=e3,
            moving_piece=e_pawn,
            move_type=MoveType.NORMAL,
        ),
    )
    child_b = StateTransition.apply(
        state,
        Move(
            from_position=d2,
            to_position=d3,
            moving_piece=d_pawn,
            move_type=MoveType.NORMAL,
        ),
    )

    assert child_a.board.get_piece(e3) == e_pawn
    assert child_a.board.get_piece(d2) == d_pawn
    assert child_b.board.get_piece(d3) == d_pawn
    assert child_b.board.get_piece(e2) == e_pawn
    assert state.board.get_piece(e2) == e_pawn
    assert state.board.get_piece(d2) == d_pawn


def test_apply_rejects_empty_source() -> None:
    state = _base_state()
    with pytest.raises(IllegalStateTransitionError):
        StateTransition.apply(
            state,
            Move(
                from_position=Position.from_chess_notation("e2"),
                to_position=Position.from_chess_notation("e3"),
                moving_piece=Piece(type=PieceType.PAWN, color=Color.WHITE),
                move_type=MoveType.NORMAL,
            ),
        )
