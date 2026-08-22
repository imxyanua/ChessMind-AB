"""Pure geometry helpers for the graphical board (testable without Tk)."""

from __future__ import annotations

from chessmind_ab.domain.position import InvalidPositionError, Position


class BoardGeometry:
    def __init__(self, square_size: int = 72, margin: int = 24) -> None:
        if square_size <= 0:
            raise ValueError("square_size must be positive")
        if margin < 0:
            raise ValueError("margin must be >= 0")
        self.square_size = square_size
        self.margin = margin

    @property
    def board_pixels(self) -> int:
        return self.square_size * 8

    def position_to_pixels(self, position: Position) -> tuple[int, int, int, int]:
        x0 = self.margin + position.column * self.square_size
        y0 = self.margin + position.row * self.square_size
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
        return Position(row=int(row), column=int(column))
