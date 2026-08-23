"""Chess board widget for PySide6."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.position import Position
from chessmind_ab.presentation.board_geometry import BoardGeometry
from chessmind_ab.presentation.qt_pieces import QtPieceCache
from chessmind_ab.presentation.themes import BOARD_THEMES, BoardTheme


class ChessBoardWidget(QWidget):
    square_clicked = Signal(object)  # Position

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.geometry_helper = BoardGeometry(square_size=72, margin=30, flipped=False)
        self.pieces = QtPieceCache(self.geometry_helper.square_size)
        self.board_theme: BoardTheme = BOARD_THEMES["green"]
        self.chrome_bg: str | None = None
        self.state: GameState | None = None
        self.selected: Position | None = None
        self.targets: set[Position] = set()
        self.captures: set[Position] = set()
        self.last_from: Position | None = None
        self.last_to: Position | None = None
        self.checked: Position | None = None
        self.hover: Position | None = None
        self.hidden: set[Position] = set()
        self._float_piece = None
        self._float_pos: QPoint | None = None
        self.setMouseTracking(True)
        size = (
            self.geometry_helper.board_pixels
            + self.geometry_helper.margin * 2
        )
        self.setFixedSize(size, size)

    def set_flipped(self, flipped: bool) -> None:
        self.geometry_helper.flipped = flipped
        self.update()

    def set_theme(self, name: str) -> None:
        self.board_theme = BOARD_THEMES[name]
        self.update()

    def sync(
        self,
        state: GameState,
        *,
        selected: Position | None = None,
        targets: set[Position] | None = None,
        captures: set[Position] | None = None,
        last_from: Position | None = None,
        last_to: Position | None = None,
        checked: Position | None = None,
    ) -> None:
        self.state = state
        self.selected = selected
        self.targets = targets or set()
        self.captures = captures or set()
        self.last_from = last_from
        self.last_to = last_to
        self.checked = checked
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        try:
            pos = self.geometry_helper.pixels_to_position(int(event.position().x()), int(event.position().y()))
        except Exception:
            return
        self.square_clicked.emit(pos)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        try:
            hover = self.geometry_helper.pixels_to_position(
                int(event.position().x()), int(event.position().y())
            )
        except Exception:
            hover = None
        if hover != self.hover:
            self.hover = hover
            self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.hover = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = self.board_theme
        margin = self.geometry_helper.margin
        board = self.geometry_helper.board_pixels

        painter.fillRect(self.rect(), QColor(self.chrome_bg or theme.canvas_bg))
        outer = 10
        painter.setPen(QPen(QColor(theme.frame_border), 2))
        painter.setBrush(QColor(theme.frame))
        painter.drawRect(
            margin - outer,
            margin - outer,
            board + outer * 2,
            board + outer * 2,
        )

        if self.state is None:
            return

        for row in range(8):
            for column in range(8):
                position = Position(row=row, column=column)
                x0, y0, x1, y1 = self.geometry_helper.position_to_pixels(position)
                base = theme.light if (row + column) % 2 == 0 else theme.dark
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(base))

                if position in {self.last_from, self.last_to}:
                    painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(theme.last))
                if position == self.selected:
                    painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(theme.select))
                    painter.setPen(QPen(QColor(theme.select), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4)
                if position == self.checked:
                    painter.fillRect(x0, y0, x1 - x0, y1 - y0, QColor(theme.check))

                if self.hover == position and position != self.selected:
                    painter.setPen(QPen(QColor(theme.hover), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4)

                drow, dcol = self.geometry_helper.display_row_column(position)
                painter.setPen(QColor(theme.coord))
                font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
                painter.setFont(font)
                if dcol == 0:
                    painter.drawText(
                        QRect(0, y0, margin, y1 - y0),
                        Qt.AlignmentFlag.AlignCenter,
                        str(8 - position.row),
                    )
                if drow == 7:
                    painter.drawText(
                        QRect(x0, margin + board, x1 - x0, margin),
                        Qt.AlignmentFlag.AlignCenter,
                        chr(ord("a") + position.column),
                    )

                if position in self.targets:
                    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                    if position in self.captures:
                        painter.setPen(QPen(QColor(theme.hint_capture), 3))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        inset = max(7, self.geometry_helper.square_size // 10)
                        painter.drawEllipse(
                            x0 + inset,
                            y0 + inset,
                            x1 - x0 - inset * 2,
                            y1 - y0 - inset * 2,
                        )
                    else:
                        r = max(7, self.geometry_helper.square_size // 7)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QColor(theme.hint))
                        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

                if position in self.hidden:
                    continue
                piece = self.state.board.get_piece(position)
                if piece is not None:
                    pixmap = self.pieces.get(piece)
                    px = (x0 + x1 - pixmap.width()) // 2
                    py = (y0 + y1 - pixmap.height()) // 2 + 1
                    painter.drawPixmap(px, py, pixmap)

        if self._float_piece is not None and self._float_pos is not None:
            pixmap = self.pieces.get(self._float_piece)
            painter.drawPixmap(
                self._float_pos.x() - pixmap.width() // 2,
                self._float_pos.y() - pixmap.height() // 2,
                pixmap,
            )
