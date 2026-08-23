"""Shared UI helpers used by geometry tests and GUIs."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType

_PIECE_GLYPHS = {
    (PieceType.KING, Color.WHITE): "♔",
    (PieceType.QUEEN, Color.WHITE): "♕",
    (PieceType.ROOK, Color.WHITE): "♖",
    (PieceType.BISHOP, Color.WHITE): "♗",
    (PieceType.KNIGHT, Color.WHITE): "♘",
    (PieceType.PAWN, Color.WHITE): "♙",
    (PieceType.KING, Color.BLACK): "♚",
    (PieceType.QUEEN, Color.BLACK): "♛",
    (PieceType.ROOK, Color.BLACK): "♜",
    (PieceType.BISHOP, Color.BLACK): "♝",
    (PieceType.KNIGHT, Color.BLACK): "♞",
    (PieceType.PAWN, Color.BLACK): "♟",
}


def piece_glyph(piece: Piece) -> str:
    return _PIECE_GLYPHS[(piece.type, piece.color)]


def format_status(status: GameStatus) -> str:
    return status.name.replace("_", " ").title()
