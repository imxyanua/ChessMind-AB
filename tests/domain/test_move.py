"""Unit tests for Move invariants (P1-4)."""

import pytest

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.move import InvalidMoveError, Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def _white_pawn() -> Piece:
    return Piece(type=PieceType.PAWN, color=Color.WHITE)


def _black_knight() -> Piece:
    return Piece(type=PieceType.KNIGHT, color=Color.BLACK)


def test_normal_move() -> None:
    move = Move(
        from_position=Position.from_chess_notation("e2"),
        to_position=Position.from_chess_notation("e3"),
        moving_piece=_white_pawn(),
        move_type=MoveType.NORMAL,
    )
    assert move.move_type is MoveType.NORMAL
    assert move.captured_piece is None
    assert move.promotion_piece is None


def test_capture_move_requires_captured_piece() -> None:
    move = Move(
        from_position=Position.from_chess_notation("e4"),
        to_position=Position.from_chess_notation("d5"),
        moving_piece=_white_pawn(),
        move_type=MoveType.CAPTURE,
        captured_piece=_black_knight(),
    )
    assert move.captured_piece == _black_knight()


def test_pawn_double_move() -> None:
    move = Move(
        from_position=Position.from_chess_notation("e2"),
        to_position=Position.from_chess_notation("e4"),
        moving_piece=_white_pawn(),
        move_type=MoveType.PAWN_DOUBLE,
    )
    assert move.move_type is MoveType.PAWN_DOUBLE


@pytest.mark.parametrize(
    "promotion_piece",
    [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT],
)
def test_promotion_move_accepts_valid_pieces(promotion_piece: PieceType) -> None:
    move = Move(
        from_position=Position.from_chess_notation("e7"),
        to_position=Position.from_chess_notation("e8"),
        moving_piece=_white_pawn(),
        move_type=MoveType.PROMOTION,
        promotion_piece=promotion_piece,
    )
    assert move.promotion_piece is promotion_piece


def test_promotion_capture_move() -> None:
    move = Move(
        from_position=Position.from_chess_notation("e7"),
        to_position=Position.from_chess_notation("d8"),
        moving_piece=_white_pawn(),
        move_type=MoveType.PROMOTION_CAPTURE,
        captured_piece=Piece(type=PieceType.ROOK, color=Color.BLACK),
        promotion_piece=PieceType.QUEEN,
    )
    assert move.move_type is MoveType.PROMOTION_CAPTURE


def test_from_equals_to_is_rejected() -> None:
    square = Position.from_chess_notation("e2")
    with pytest.raises(InvalidMoveError):
        Move(
            from_position=square,
            to_position=square,
            moving_piece=_white_pawn(),
            move_type=MoveType.NORMAL,
        )


@pytest.mark.parametrize("bad", [PieceType.KING, PieceType.PAWN])
def test_promotion_to_king_or_pawn_is_rejected(bad: PieceType) -> None:
    with pytest.raises(InvalidMoveError):
        Move(
            from_position=Position.from_chess_notation("e7"),
            to_position=Position.from_chess_notation("e8"),
            moving_piece=_white_pawn(),
            move_type=MoveType.PROMOTION,
            promotion_piece=bad,
        )


def test_promotion_without_piece_is_rejected() -> None:
    with pytest.raises(InvalidMoveError):
        Move(
            from_position=Position.from_chess_notation("e7"),
            to_position=Position.from_chess_notation("e8"),
            moving_piece=_white_pawn(),
            move_type=MoveType.PROMOTION,
        )
