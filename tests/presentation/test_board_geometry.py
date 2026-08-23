"""Unit tests for graphical board geometry."""

import pytest

from chessmind_ab.domain.position import InvalidPositionError, Position
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.presentation.board_geometry import BoardGeometry
from chessmind_ab.presentation.ui_common import piece_glyph


def test_position_pixel_roundtrip_center() -> None:
    geo = BoardGeometry(square_size=72, margin=28)
    position = Position.from_chess_notation("e4")
    x0, y0, x1, y1 = geo.position_to_pixels(position)
    center_x = (x0 + x1) // 2
    center_y = (y0 + y1) // 2
    assert geo.pixels_to_position(center_x, center_y) == position


def test_a8_and_h1_corners() -> None:
    geo = BoardGeometry(square_size=72, margin=28)
    a8 = Position.from_chess_notation("a8")
    h1 = Position.from_chess_notation("h1")
    ax0, ay0, _, _ = geo.position_to_pixels(a8)
    assert geo.pixels_to_position(ax0 + 1, ay0 + 1) == a8
    hx0, hy0, hx1, hy1 = geo.position_to_pixels(h1)
    assert geo.pixels_to_position(hx1 - 1, hy1 - 1) == h1


def test_click_outside_board_rejected() -> None:
    geo = BoardGeometry(square_size=72, margin=28)
    with pytest.raises(InvalidPositionError):
        geo.pixels_to_position(0, 0)


def test_flipped_board_maps_a8_to_bottom_right_visual() -> None:
    geo = BoardGeometry(square_size=72, margin=28, flipped=True)
    a8 = Position.from_chess_notation("a8")
    x0, y0, x1, y1 = geo.position_to_pixels(a8)
    # Flipped: a8 appears at bottom-right visually.
    assert x0 > geo.margin + 6 * geo.square_size
    assert y0 > geo.margin + 6 * geo.square_size
    assert geo.pixels_to_position((x0 + x1) // 2, (y0 + y1) // 2) == a8


def test_piece_glyph_maps_king() -> None:
    assert piece_glyph(Piece(type=PieceType.KING, color=Color.WHITE)) == "♔"
    assert piece_glyph(Piece(type=PieceType.KING, color=Color.BLACK)) == "♚"


def test_format_status_prettifies_enum() -> None:
    from chessmind_ab.domain.game_status import GameStatus
    from chessmind_ab.presentation.ui_common import format_status

    assert format_status(GameStatus.WHITE_WINS_CHECKMATE) == "White Wins Checkmate"
