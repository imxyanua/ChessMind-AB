"""Shared piece asset path helpers (framework-agnostic)."""

from __future__ import annotations

from pathlib import Path

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType

_TYPE_NAMES = {
    PieceType.PAWN: "pawn",
    PieceType.KNIGHT: "knight",
    PieceType.BISHOP: "bishop",
    PieceType.ROOK: "rook",
    PieceType.QUEEN: "queen",
    PieceType.KING: "king",
}


def assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "pieces"


def piece_filename(piece: Piece) -> str:
    color = "white" if piece.color is Color.WHITE else "black"
    return f"{color}_{_TYPE_NAMES[piece.type]}.png"
