"""Board square with fixed row/column and chess notation."""

from __future__ import annotations

from dataclasses import dataclass


class InvalidPositionError(ValueError):
    """Raised when row/column or chess notation is invalid."""


@dataclass(frozen=True, slots=True)
class Position:
    row: int
    column: int

    def __post_init__(self) -> None:
        if not self.is_valid():
            raise InvalidPositionError(
                f"Position out of range: row={self.row}, column={self.column}"
            )

    def is_valid(self) -> bool:
        return 0 <= self.row < 8 and 0 <= self.column < 8

    def to_chess_notation(self) -> str:
        file_char = chr(ord("a") + self.column)
        rank_char = str(8 - self.row)
        return f"{file_char}{rank_char}"

    @classmethod
    def from_chess_notation(cls, notation: str) -> Position:
        if not isinstance(notation, str) or len(notation) != 2:
            raise InvalidPositionError(f"Invalid chess notation: {notation!r}")

        file_char = notation[0]
        rank_char = notation[1]
        if file_char < "a" or file_char > "h" or rank_char < "1" or rank_char > "8":
            raise InvalidPositionError(f"Invalid chess notation: {notation!r}")

        column = ord(file_char) - ord("a")
        row = 8 - int(rank_char)
        return cls(row=row, column=column)
