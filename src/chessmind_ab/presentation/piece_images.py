"""Load and cache PNG piece sprites for Tkinter."""

from __future__ import annotations

import tempfile
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
        self._temp_files: list[Path] = []

    def get(self, piece: Piece) -> tk.PhotoImage:
        key = f"{piece.color.name}:{piece.type.name}:{self._square_size}"
        cached = self._images.get(key)
        if cached is not None:
            return cached

        path = assets_dir() / piece_filename(piece)
        if not path.exists():
            raise FileNotFoundError(f"Missing piece sprite: {path}")

        target = max(24, self._square_size - 10)
        image = self._load_scaled(path, target)
        self._images[key] = image
        return image

    def _load_scaled(self, path: Path, target: int) -> tk.PhotoImage:
        try:
            from PIL import Image

            src = Image.open(path).convert("RGBA")
            if src.size != (target, target):
                src = src.resize((target, target), Image.Resampling.LANCZOS)
            tmp = Path(tempfile.mkstemp(suffix=".png")[1])
            src.save(tmp)
            self._temp_files.append(tmp)
            return tk.PhotoImage(file=str(tmp))
        except Exception:
            # Fallback without Pillow: nearest-neighbor via zoom/subsample.
            image = tk.PhotoImage(file=str(path))
            width = max(1, int(image.width()))
            if width == target:
                return image
            if width < target:
                factor = max(1, target // width)
                return image.zoom(factor, factor)
            factor = max(1, width // target)
            return image.subsample(factor, factor)
