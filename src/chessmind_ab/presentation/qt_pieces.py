"""QPixmap piece cache for the PySide6 GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from chessmind_ab.domain.piece import Piece
from chessmind_ab.presentation.piece_images import assets_dir, piece_filename


class QtPieceCache:
    def __init__(self, square_size: int) -> None:
        self._square_size = square_size
        self._images: dict[str, QPixmap] = {}

    def get(self, piece: Piece) -> QPixmap:
        key = f"{piece.color.name}:{piece.type.name}:{self._square_size}"
        cached = self._images.get(key)
        if cached is not None:
            return cached

        path = assets_dir() / piece_filename(piece)
        if not path.exists():
            raise FileNotFoundError(f"Missing piece sprite: {path}")

        target = max(28, self._square_size - 8)
        pixmap = QPixmap(str(path))
        scaled = pixmap.scaled(
            target,
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._images[key] = scaled
        return scaled
