"""Unit tests for Piece and Board (P1-3)."""

import pytest

from chessmind_ab.domain.board import Board, KingNotFoundError
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def test_piece_stores_type_and_color_only() -> None:
    piece = Piece(type=PieceType.QUEEN, color=Color.WHITE)
    assert piece.type is PieceType.QUEEN
    assert piece.color is Color.WHITE
    assert not hasattr(piece, "generate_moves")


def test_board_get_set_remove_piece() -> None:
    board = Board()
    e2 = Position.from_chess_notation("e2")
    pawn = Piece(type=PieceType.PAWN, color=Color.WHITE)

    assert board.get_piece(e2) is None
    board.set_piece(e2, pawn)
    assert board.get_piece(e2) == pawn

    removed = board.remove_piece(e2)
    assert removed == pawn
    assert board.get_piece(e2) is None


def test_board_find_king() -> None:
    board = Board()
    e1 = Position.from_chess_notation("e1")
    e8 = Position.from_chess_notation("e8")
    board.set_piece(e1, Piece(type=PieceType.KING, color=Color.WHITE))
    board.set_piece(e8, Piece(type=PieceType.KING, color=Color.BLACK))

    assert board.find_king(Color.WHITE) == e1
    assert board.find_king(Color.BLACK) == e8


def test_board_find_king_missing_raises() -> None:
    board = Board()
    with pytest.raises(KingNotFoundError):
        board.find_king(Color.WHITE)


def test_board_copy_isolation() -> None:
    board = Board()
    a1 = Position.from_chess_notation("a1")
    h8 = Position.from_chess_notation("h8")
    board.set_piece(a1, Piece(type=PieceType.ROOK, color=Color.WHITE))

    cloned = board.copy()
    cloned.set_piece(h8, Piece(type=PieceType.QUEEN, color=Color.BLACK))
    cloned.remove_piece(a1)

    assert board.get_piece(a1) == Piece(type=PieceType.ROOK, color=Color.WHITE)
    assert board.get_piece(h8) is None
    assert cloned.get_piece(a1) is None
    assert cloned.get_piece(h8) == Piece(type=PieceType.QUEEN, color=Color.BLACK)
