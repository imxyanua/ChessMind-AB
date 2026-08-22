"""Asset and theme smoke tests."""

import tkinter as tk

import pytest

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.presentation.piece_images import (
    PieceImageCache,
    assets_dir,
    piece_filename,
)
from chessmind_ab.presentation.themes import BOARD_THEMES, UI_THEMES


def test_all_piece_sprites_exist() -> None:
    root = assets_dir()
    assert root.is_dir()
    for color in (Color.WHITE, Color.BLACK):
        for piece_type in PieceType:
            piece = Piece(type=piece_type, color=color)
            path = root / piece_filename(piece)
            assert path.exists(), path
            assert path.stat().st_size > 0


def test_theme_packs_available() -> None:
    assert set(BOARD_THEMES) >= {"green", "wood"}
    assert set(UI_THEMES) >= {"dark", "light"}
    for theme in BOARD_THEMES.values():
        assert theme.frame
        assert theme.frame_border
        assert theme.hover
        assert theme.hint
        assert theme.hint_capture


def test_piece_image_cache_loads_with_shadow() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk not available: {exc}")
    root.withdraw()
    try:
        cache = PieceImageCache(square_size=88)
        piece = Piece(type=PieceType.KNIGHT, color=Color.WHITE)
        image = cache.get(piece)
        assert int(image.width()) >= 80
        assert int(image.height()) >= 80
        again = cache.get(piece)
        assert again is image
    finally:
        root.destroy()
