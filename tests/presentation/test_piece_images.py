"""Asset and theme smoke tests."""

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.presentation.piece_images import assets_dir, piece_filename
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
    for theme in UI_THEMES.values():
        assert theme.card_bg
        assert theme.card_border
        assert theme.accent_soft
        assert theme.list_bg
        assert theme.row_alt
        assert theme.input_bg
        assert theme.button_bg
        # Basic contrast sanity: text != background.
        assert theme.text.lower() != theme.card_bg.lower()
        assert theme.text.lower() != theme.app_bg.lower()
