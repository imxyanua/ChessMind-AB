"""Unit tests for domain enums (P1-1)."""

from chessmind_ab.domain import Color, GameStatus, MoveType, PieceType


def test_color_has_white_and_black() -> None:
    assert {member.name for member in Color} == {"WHITE", "BLACK"}


def test_color_opposite_switches_sides() -> None:
    assert Color.WHITE.opposite() is Color.BLACK
    assert Color.BLACK.opposite() is Color.WHITE


def test_piece_type_core_set() -> None:
    assert {member.name for member in PieceType} == {
        "PAWN",
        "KNIGHT",
        "BISHOP",
        "ROOK",
        "QUEEN",
        "KING",
    }


def test_game_status_core_set() -> None:
    assert {member.name for member in GameStatus} == {
        "ONGOING",
        "WHITE_WINS_CHECKMATE",
        "BLACK_WINS_CHECKMATE",
        "STALEMATE",
        "DRAW",
    }


def test_move_type_core_set() -> None:
    assert {member.name for member in MoveType} == {
        "NORMAL",
        "CAPTURE",
        "PAWN_DOUBLE",
        "PROMOTION",
        "PROMOTION_CAPTURE",
    }


def test_domain_package_reexports_enums() -> None:
    import chessmind_ab.domain as domain

    assert domain.Color is Color
    assert domain.PieceType is PieceType
    assert domain.GameStatus is GameStatus
    assert domain.MoveType is MoveType
