"""Load and cache PNG piece sprites for Tkinter."""

from __future__ import annotations

from pathlib import Path

import tkinter as tk

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


class PieceImageCache:
    def __init__(self, square_size: int) -> None:
        self._square_size = square_size
        self._images: dict[str, tk.PhotoImage] = {}

    def get(self, piece: Piece) -> tk.PhotoImage:
        key = f"{piece.color.name}:{piece.type.name}:{self._square_size}"
        cached = self._images.get(key)
        if cached is not None:
            return cached

        path = assets_dir() / piece_filename(piece)
        if not path.exists():
            raise FileNotFoundError(f"Missing piece sprite: {path}")

        image = tk.PhotoImage(file=str(path))
        # PhotoImage subsample/zoom only supports integers; approximate size.
        target = max(24, self._square_size - 12)
        # Scale down from 128px source using subsample.
        factor = max(1, round(128 / target))
        if factor > 1:
            image = image.subsample(factor, factor)
        self._images[key] = image
        return image
