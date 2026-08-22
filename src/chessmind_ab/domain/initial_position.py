"""Standard chess starting position for core rules."""

from __future__ import annotations

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position

_BACK_RANK = [
    PieceType.ROOK,
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.QUEEN,
    PieceType.KING,
    PieceType.BISHOP,
    PieceType.KNIGHT,
    PieceType.ROOK,
]


def create_initial_game_state() -> GameState:
    board = Board()
    for column, piece_type in enumerate(_BACK_RANK):
        board.set_piece(
            Position(row=7, column=column),
            Piece(type=piece_type, color=Color.WHITE),
        )
        board.set_piece(
            Position(row=0, column=column),
            Piece(type=piece_type, color=Color.BLACK),
        )
        board.set_piece(
            Position(row=6, column=column),
            Piece(type=PieceType.PAWN, color=Color.WHITE),
        )
        board.set_piece(
            Position(row=1, column=column),
            Piece(type=PieceType.PAWN, color=Color.BLACK),
        )
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )
