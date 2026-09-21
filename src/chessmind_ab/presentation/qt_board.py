"""Chess board widget for PySide6."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.position import Position
from chessmind_ab.presentation.board_geometry import BoardGeometry
from chessmind_ab.presentation.qt_pieces import QtPieceCache
from chessmind_ab.presentation.themes import BOARD_THEMES, BoardTheme


def _ease_out_cubic(t: float) -> float:
    u = 1.0 - t
    return 1.0 - u * u * u


@dataclass
class _FloatSlide:
    piece: Piece
    start: QPoint
    end: QPoint
    pos: QPoint


class ChessBoardWidget(QWidget):
    square_clicked = Signal(object)  # Position
    animation_finished = Signal()

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
        self._slides: list[_FloatSlide] = []
        self._anim_elapsed_ms = 0
        self._anim_duration_ms = 0
        self._anim_callback: Callable[[], None] | None = None
        self._board_spin = 0.0
        self._pending_flipped: bool | None = None
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._on_anim_tick)
        self.setMouseTracking(True)
        size = (
            self.geometry_helper.board_pixels
            + self.geometry_helper.margin * 2
        )
        self.setFixedSize(size, size)

    @property
    def is_animating(self) -> bool:
        return self._anim_timer.isActive()

    @property
    def _float_piece(self) -> Piece | None:
        """Primary floating piece (compat for smoke tests)."""
        return self._slides[0].piece if self._slides else None

    def set_flipped(self, flipped: bool) -> None:
        self.geometry_helper.flipped = flipped
        self._board_spin = 0.0
        self._pending_flipped = None
        self.update()

    def animate_viewpoint_flip(
        self,
        flipped: bool,
        *,
        on_finished: Callable[[], None] | None = None,
        duration_ms: int = 520,
    ) -> None:
        """Rotate the viewpoint 180 degrees like chess.com (player stays at the bottom).

        Squares spin with the board. Piece sprites stay upright and slide to the
        new screen seats. ``flipped`` is applied when the motion finishes.
        """
        if self.geometry_helper.flipped is flipped:
            if on_finished is not None:
                on_finished()
            return

        self.cancel_animation(run_callback=False)
        if self.state is None:
            self.set_flipped(flipped)
            if on_finished is not None:
                on_finished()
            return

        old_flipped = self.geometry_helper.flipped
        slides: list[_FloatSlide] = []
        hidden: set[Position] = set()
        for row in range(8):
            for column in range(8):
                position = Position(row=row, column=column)
                piece = self.state.board.get_piece(position)
                if piece is None:
                    continue
                start = self._square_center(position)
                self.geometry_helper.flipped = flipped
                end = self._square_center(position)
                self.geometry_helper.flipped = old_flipped
                slides.append(
                    _FloatSlide(piece=piece, start=start, end=end, pos=QPoint(start))
                )
                hidden.add(position)

        self._slides = slides
        self.hidden = hidden
        self._board_spin = 0.0
        self._pending_flipped = flipped
        self._anim_elapsed_ms = 0
        self._anim_duration_ms = max(1, duration_ms)
        self._anim_callback = on_finished
        self.update()
        self._anim_timer.start()

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

    def _square_center(self, position: Position) -> QPoint:
        x0, y0, x1, y1 = self.geometry_helper.position_to_pixels(position)
        return QPoint((x0 + x1) // 2, (y0 + y1) // 2)

    def animate_move(
        self,
        piece: Piece,
        from_pos: Position,
        to_pos: Position,
        *,
        on_finished: Callable[[], None] | None = None,
        duration_ms: int | None = None,
        extra_slides: Sequence[tuple[Piece, Position, Position]] | None = None,
    ) -> None:
        """Slide ``piece`` from ``from_pos`` to ``to_pos`` (ease-out).

        ``extra_slides`` animates additional pieces in parallel (castling rook).
        """
        slides: list[tuple[Piece, Position, Position]] = [(piece, from_pos, to_pos)]
        if extra_slides:
            slides.extend(extra_slides)
        self.animate_slides(
            slides, on_finished=on_finished, duration_ms=duration_ms
        )

    def animate_slides(
        self,
        slides: Sequence[tuple[Piece, Position, Position]],
        *,
        on_finished: Callable[[], None] | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Slide one or more pieces in parallel with a shared ease-out clock."""
        if not slides:
            if on_finished is not None:
                on_finished()
            return

        self.cancel_animation(run_callback=False)
        float_slides: list[_FloatSlide] = []
        hidden: set[Position] = set()
        max_distance = 0.0
        for piece, from_pos, to_pos in slides:
            start = self._square_center(from_pos)
            end = self._square_center(to_pos)
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            max_distance = max(max_distance, (dx * dx + dy * dy) ** 0.5)
            float_slides.append(
                _FloatSlide(piece=piece, start=start, end=end, pos=QPoint(start))
            )
            hidden.add(from_pos)
            hidden.add(to_pos)

        if duration_ms is None:
            duration_ms = int(max(140, min(280, 110 + max_distance * 0.35)))

        self._slides = float_slides
        self._anim_elapsed_ms = 0
        self._anim_duration_ms = max(1, duration_ms)
        self._anim_callback = on_finished
        self.hidden = hidden
        self.update()
        self._anim_timer.start()

    def cancel_animation(self, *, run_callback: bool = False) -> None:
        was_active = self._anim_timer.isActive()
        self._anim_timer.stop()
        callback = self._anim_callback
        self._anim_callback = None
        self._slides = []
        self._anim_elapsed_ms = 0
        self._anim_duration_ms = 0
        self.hidden = set()
        if self._pending_flipped is not None:
            self.geometry_helper.flipped = self._pending_flipped
            self._pending_flipped = None
        self._board_spin = 0.0
        if was_active:
            self.update()
        if run_callback and callback is not None:
            callback()

    def _on_anim_tick(self) -> None:
        if not self._slides and self._pending_flipped is None:
            self.cancel_animation(run_callback=True)
            return
        self._anim_elapsed_ms += self._anim_timer.interval()
        t = min(1.0, self._anim_elapsed_ms / self._anim_duration_ms)
        e = _ease_out_cubic(t)
        if self._pending_flipped is not None:
            self._board_spin = 180.0 * e
        for slide in self._slides:
            x = slide.start.x() + (slide.end.x() - slide.start.x()) * e
            y = slide.start.y() + (slide.end.y() - slide.start.y()) * e
            slide.pos = QPoint(int(round(x)), int(round(y)))
        self.update()
        if t >= 1.0:
            self._finish_animation()

    def _finish_animation(self) -> None:
        callback = self._anim_callback
        self._anim_timer.stop()
        self._anim_callback = None
        self._slides = []
        self._anim_elapsed_ms = 0
        self._anim_duration_ms = 0
        self.hidden = set()
        if self._pending_flipped is not None:
            self.geometry_helper.flipped = self._pending_flipped
            self._pending_flipped = None
        self._board_spin = 0.0
        self.update()
        self.animation_finished.emit()
        if callback is not None:
            callback()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self.is_animating:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        try:
            pos = self.geometry_helper.pixels_to_position(
                int(event.position().x()), int(event.position().y())
            )
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

        spinning = abs(self._board_spin) > 0.01
        if spinning:
            center_x = margin + board / 2
            center_y = margin + board / 2
            painter.save()
            painter.translate(center_x, center_y)
            painter.rotate(self._board_spin)
            painter.translate(-center_x, -center_y)

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

                if not spinning:
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

        if spinning:
            painter.restore()

        for slide in self._slides:
            pixmap = self.pieces.get(slide.piece)
            painter.drawPixmap(
                slide.pos.x() - pixmap.width() // 2,
                slide.pos.y() - pixmap.height() // 2,
                pixmap,
            )
