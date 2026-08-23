"""Pure geometry helpers for the graphical board (testable without Tk)."""

from __future__ import annotations

from chessmind_ab.domain.position import InvalidPositionError, Position


class BoardGeometry:
    def __init__(
        self, square_size: int = 72, margin: int = 24, *, flipped: bool = False
    ) -> None:
        if square_size <= 0:
            raise ValueError("square_size must be positive")
        if margin < 0:
            raise ValueError("margin must be >= 0")
        self.square_size = square_size
        self.margin = margin
        self.flipped = flipped

    @property
    def board_pixels(self) -> int:
        return self.square_size * 8

    def display_row_column(self, position: Position) -> tuple[int, int]:
        if self.flipped:
            return 7 - position.row, 7 - position.column
        return position.row, position.column

    def position_from_display(self, display_row: int, display_column: int) -> Position:
        if self.flipped:
            return Position(row=7 - display_row, column=7 - display_column)
        return Position(row=display_row, column=display_column)

    def position_to_pixels(self, position: Position) -> tuple[int, int, int, int]:
        row, column = self.display_row_column(position)
        x0 = self.margin + column * self.square_size
        y0 = self.margin + row * self.square_size
        x1 = x0 + self.square_size
        y1 = y0 + self.square_size
        return x0, y0, x1, y1

    def pixels_to_position(self, x: int, y: int) -> Position:
        local_x = x - self.margin
        local_y = y - self.margin
        if local_x < 0 or local_y < 0:
            raise InvalidPositionError("Click outside board")
        column = local_x // self.square_size
        row = local_y // self.square_size
        if column > 7 or row > 7:
            raise InvalidPositionError("Click outside board")
        return self.position_from_display(int(row), int(column))
