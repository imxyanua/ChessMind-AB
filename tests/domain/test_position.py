"""Unit tests for Position (P1-2)."""

import pytest

from chessmind_ab.domain.position import InvalidPositionError, Position


@pytest.mark.parametrize(
    ("notation", "row", "column"),
    [
        ("a8", 0, 0),
        ("h8", 0, 7),
        ("a1", 7, 0),
        ("h1", 7, 7),
        ("e4", 4, 4),
    ],
)
def test_from_and_to_chess_notation_roundtrip(notation: str, row: int, column: int) -> None:
    position = Position.from_chess_notation(notation)
    assert position.row == row
    assert position.column == column
    assert position.to_chess_notation() == notation


@pytest.mark.parametrize("notation", ["a0", "i5", "z9", "e9", "", "e", "e44", "A1"])
def test_invalid_notation_is_rejected(notation: str) -> None:
    with pytest.raises(InvalidPositionError):
        Position.from_chess_notation(notation)


@pytest.mark.parametrize(("row", "column"), [(-1, 0), (0, -1), (8, 0), (0, 8), (9, 9)])
def test_out_of_range_constructor_is_rejected(row: int, column: int) -> None:
    with pytest.raises(InvalidPositionError):
        Position(row=row, column=column)


def test_is_valid_true_for_in_board_square() -> None:
    assert Position(3, 3).is_valid() is True
