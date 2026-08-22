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

_SHADOW_PAD = 5


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
        key = f"{piece.color.name}:{piece.type.name}:{self._square_size}:shadow"
        cached = self._images.get(key)
        if cached is not None:
            return cached

        path = assets_dir() / piece_filename(piece)
        if not path.exists():
            raise FileNotFoundError(f"Missing piece sprite: {path}")

        # Leave a little margin inside the square for shadow room.
        target = max(28, self._square_size - 6)
        image = self._load_scaled(path, target)
        self._images[key] = image
        return image

    def _load_scaled(self, path: Path, target: int) -> tk.PhotoImage:
        try:
            from PIL import Image, ImageFilter

            src = Image.open(path).convert("RGBA")
            if src.size != (target, target):
                src = src.resize((target, target), Image.Resampling.LANCZOS)

            canvas_size = target + _SHADOW_PAD * 2
            canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))

            alpha = src.split()[3]
            shadow = Image.new("RGBA", (target, target), (0, 0, 0, 0))
            shadow.putalpha(alpha.point(lambda value: int(value * 0.42)))
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2.2))
            canvas.paste(shadow, (_SHADOW_PAD + 2, _SHADOW_PAD + 3), shadow)
            canvas.paste(src, (_SHADOW_PAD, _SHADOW_PAD), src)

            tmp = Path(tempfile.mkstemp(suffix=".png")[1])
            canvas.save(tmp)
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
