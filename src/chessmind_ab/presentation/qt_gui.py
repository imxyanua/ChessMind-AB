"""PySide6 desktop GUI for ChessMind-AB."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chessmind_ab.application.difficulty import (
    DEFAULT_DIFFICULTY_KEY,
    DIFFICULTIES,
    difficulty_from_label,
    get_difficulty,
)
from chessmind_ab.application.game_controller import GameController, material_sort_key
from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.position import Position
from chessmind_ab.presentation.qt_board import ChessBoardWidget
from chessmind_ab.presentation.themes import (
    BOARD_THEMES,
    DEFAULT_BOARD_FOR_UI,
    UI_THEMES,
    UiTheme,
)
from chessmind_ab.presentation.ui_common import format_status, piece_glyph


class AiWorker(QThread):
    finished_ok = Signal(object, object)
    finished_err = Signal(str)

    def __init__(self, controller: GameController) -> None:
        super().__init__()
        self._controller = controller

    def run(self) -> None:
        try:
            result = self._controller.make_ai_move()
            search = self._controller.get_last_search_result()
            self.finished_ok.emit(result, search)
        except Exception as exc:  # noqa: BLE001
            self.finished_err.emit(str(exc))


class ChessMainWindow(QMainWindow):
    def __init__(self, difficulty_key: str = DEFAULT_DIFFICULTY_KEY) -> None:
        super().__init__()
        self.setWindowTitle("ChessMind-AB")

        self.ui_theme: UiTheme = UI_THEMES["dark"]
        self.controller = GameController(
            difficulty_key=difficulty_key, player_color=Color.WHITE
        )
        self.controller.start_new_game()

        self.selected: Position | None = None
        self.targets: set[Position] = set()
        self.captures: set[Position] = set()
        self.last_from: Position | None = None
        self.last_to: Position | None = None
        self._ai_busy = False
        self._worker: AiWorker | None = None
        self._think_dots = 0
        self._think_timer = QTimer(self)
        self._think_timer.timeout.connect(self._on_think_tick)

        self._build()
        self._apply_theme()
        self._refresh()

    def _card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        return frame

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self.board = ChessBoardWidget()
        self.board.square_clicked.connect(self._on_square_clicked)
        layout.addWidget(self.board, 0, Qt.AlignmentFlag.AlignTop)

        # Info card
        info_card = self._card()
        info_card.setFixedWidth(320)
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)

        self.title = QLabel("ChessMind-AB")
        self.title.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        self.subtitle = QLabel("Player vs AI  ·  Elo modes")
        info_layout.addWidget(self.title)
        info_layout.addWidget(self.subtitle)

        self._section(info_layout, "GAME")
        self.mode_value = QLabel("")
        self.turn_value = QLabel("White")
        self.status_value = QLabel("Ongoing")
        self.last_value = QLabel("—")
        self.ai_value = QLabel("waiting")
        self.stats_value = QLabel("—")
        for key, label in (
            ("Mode", self.mode_value),
            ("Turn", self.turn_value),
            ("Status", self.status_value),
            ("Last", self.last_value),
            ("AI", self.ai_value),
            ("Stats", self.stats_value),
        ):
            info_layout.addLayout(self._kv(key, label))

        self.ai_badge = QLabel("")
        self.ai_badge.setObjectName("badge")
        info_layout.addWidget(self.ai_badge)

        self.captured_you = QLabel("You  —")
        self.captured_ai = QLabel("AI   —")
        info_layout.addWidget(self.captured_you)
        info_layout.addWidget(self.captured_ai)

        self._section(info_layout, "SETTINGS")
        self.side_box = QComboBox()
        self.side_box.addItems(["White", "Black"])
        info_layout.addLayout(self._labeled("Play as", self.side_box))
        self.side_box.currentTextChanged.connect(self._on_side_changed)

        self.diff_box = QComboBox()
        for diff in DIFFICULTIES.values():
            self.diff_box.addItem(diff.label, diff.key)
        current = get_difficulty(self.controller.get_difficulty().key)
        self.diff_box.setCurrentText(current.label)
        info_layout.addLayout(self._labeled("Difficulty", self.diff_box))
        self.diff_box.currentTextChanged.connect(self._on_difficulty_changed)

        self.diff_desc = QLabel(current.description)
        self.diff_desc.setObjectName("key")
        self.diff_desc.setWordWrap(True)
        self.diff_desc.setFixedHeight(48)
        self.diff_desc.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(self.diff_desc)

        self.board_theme_box = QComboBox()
        self.board_theme_box.addItems(list(BOARD_THEMES.keys()))
        info_layout.addLayout(self._labeled("Board", self.board_theme_box))
        self.board_theme_box.currentTextChanged.connect(self._on_board_theme)

        self.ui_theme_box = QComboBox()
        self.ui_theme_box.addItems(list(UI_THEMES.keys()))
        info_layout.addLayout(self._labeled("UI", self.ui_theme_box))
        self.ui_theme_box.currentTextChanged.connect(self._on_ui_theme)

        self._section(info_layout, "ACTIONS")
        btn_row = QHBoxLayout()
        self.new_btn = QPushButton("New Game")
        self.undo_btn = QPushButton("Undo")
        self.new_btn.clicked.connect(self._on_new_game)
        self.undo_btn.clicked.connect(self._on_undo)
        btn_row.addWidget(self.new_btn)
        btn_row.addWidget(self.undo_btn)
        info_layout.addLayout(btn_row)

        pgn_row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy PGN")
        self.save_btn = QPushButton("Save PGN")
        self.copy_btn.clicked.connect(self._on_copy_pgn)
        self.save_btn.clicked.connect(self._on_save_pgn)
        pgn_row.addWidget(self.copy_btn)
        pgn_row.addWidget(self.save_btn)
        info_layout.addLayout(pgn_row)
        info_layout.addStretch(1)
        layout.addWidget(info_card, 0, Qt.AlignmentFlag.AlignTop)

        # History card
        hist_card = self._card()
        hist_card.setFixedWidth(300)
        hist_layout = QVBoxLayout(hist_card)
        hist_title = QLabel("Move list")
        hist_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        hist_sub = QLabel("SAN notation")
        hist_layout.addWidget(hist_title)
        hist_layout.addWidget(hist_sub)
        self.move_list = QListWidget()
        self.move_list.setFont(QFont("Consolas", 11))
        hist_layout.addWidget(self.move_list, 1)
        self.hint = QLabel("Click your piece, then a marked square.")
        self.hint.setObjectName("key")
        self.hint.setWordWrap(True)
        self.hint.setFixedHeight(48)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignTop)
        hist_layout.addWidget(self.hint)
        layout.addWidget(hist_card, 0, Qt.AlignmentFlag.AlignTop)

        self.setFixedSize(self.sizeHint())

    def _section(self, layout: QVBoxLayout, title: str) -> None:
        label = QLabel(title)
        label.setObjectName("section")
        layout.addWidget(label)

    def _kv(self, key: str, value: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        k = QLabel(key)
        k.setObjectName("key")
        k.setFixedWidth(56)
        row.addWidget(k)
        row.addWidget(value, 1)
        return row

    def _labeled(self, key: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        k = QLabel(key)
        k.setObjectName("key")
        row.addWidget(k)
        row.addWidget(widget, 1)
        return row

    def _apply_theme(self) -> None:
        t = self.ui_theme
        self.board.chrome_bg = t.app_bg
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {t.app_bg};
                color: {t.text};
                font-family: 'Segoe UI';
            }}
            QFrame#card {{
                background: {t.card_bg};
                border: 1px solid {t.card_border};
                border-radius: 10px;
            }}
            QLabel {{ background: transparent; color: {t.text}; }}
            QLabel#key, QLabel#section {{ color: {t.muted}; }}
            QLabel#section {{
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.6px;
                margin-top: 10px;
            }}
            QLabel#badge {{
                color: {t.accent};
                background: {t.accent_soft};
                padding: 6px 8px;
                border-radius: 6px;
            }}
            QComboBox, QListWidget {{
                background: {t.input_bg};
                color: {t.text};
                border: 1px solid {t.input_border};
                padding: 6px 8px;
                border-radius: 6px;
                selection-background-color: {t.accent};
                selection-color: #ffffff;
            }}
            QComboBox QAbstractItemView {{
                background: {t.card_bg};
                color: {t.text};
                border: 1px solid {t.input_border};
                selection-background-color: {t.accent};
                selection-color: #ffffff;
            }}
            QPushButton {{
                background: {t.button_bg};
                color: {t.text};
                border: 1px solid {t.input_border};
                padding: 8px 10px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {t.button_hover};
                border-color: {t.accent};
            }}
            QPushButton:disabled {{
                color: {t.muted};
                background: {t.list_bg};
            }}
            QListWidget {{
                background: {t.list_bg};
                outline: none;
            }}
            QListWidget::item {{
                padding: 4px 6px;
                color: {t.text};
            }}
            QListWidget::item:selected {{
                background: {t.accent};
                color: #ffffff;
            }}
            """
        )
        self.board.update()

    def _busy(self) -> bool:
        return self._ai_busy

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self.side_box,
            self.diff_box,
            self.board_theme_box,
            self.ui_theme_box,
            self.new_btn,
            self.undo_btn,
            self.copy_btn,
            self.save_btn,
        ):
            widget.setEnabled(enabled)

    def _checked_square(self) -> Position | None:
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            return None
        if AttackDetector.is_king_in_check(state, state.side_to_move):
            return state.board.find_king(state.side_to_move)
        return None

    def _format_captured(self, pieces: list[Piece]) -> str:
        if not pieces:
            return "—"
        ordered = sorted(pieces, key=material_sort_key)
        return " ".join(piece_glyph(piece) for piece in ordered)

    def _refresh(self, message: str | None = None) -> None:
        state = self.controller.get_state()
        diff = self.controller.get_difficulty()
        self.mode_value.setText(diff.label)
        self.turn_value.setText(
            "White" if state.side_to_move is Color.WHITE else "Black"
        )
        self.status_value.setText(format_status(state.status))
        history = self.controller.get_move_history()
        self.last_value.setText(history[-1].notation if history else "—")

        search = self.controller.get_last_search_result()
        ai_entries = [entry for entry in history if not entry.by_player]
        if search is not None and ai_entries:
            self.ai_value.setText(f"{ai_entries[-1].notation}  ·  {search.best_score}")
        else:
            self.ai_value.setText("waiting")

        if search is not None:
            self.stats_value.setText(
                f"{search.statistics.nodes_visited} nodes · "
                f"{search.statistics.execution_time_ms:.0f} ms"
                + (
                    f" · d{search.statistics.max_depth_reached}"
                    if search.statistics.max_depth_reached
                    else ""
                )
            )
        else:
            self.stats_value.setText("—")

        player = self.controller.get_player_color()
        self.captured_you.setText(
            "You  " + self._format_captured(self.controller.get_captured_pieces(player))
        )
        self.captured_ai.setText(
            "AI   "
            + self._format_captured(self.controller.get_captured_pieces(player.opposite()))
        )

        self.move_list.clear()
        for index in range(0, len(history), 2):
            white = history[index].notation
            black = history[index + 1].notation if index + 1 < len(history) else ""
            item = QListWidgetItem(f"{index // 2 + 1:>2}. {white:<7} {black}")
            if (index // 2) % 2 == 1:
                item.setBackground(QColor(self.ui_theme.row_alt))
            self.move_list.addItem(item)
        if history:
            self.move_list.scrollToBottom()

        self.undo_btn.setEnabled(self.controller.can_undo() and not self._busy())
        if message is not None:
            self.hint.setText(message)

        self.board.sync(
            state,
            selected=self.selected,
            targets=self.targets,
            captures=self.captures,
            last_from=self.last_from,
            last_to=self.last_to,
            checked=self._checked_square(),
        )

    def _on_board_theme(self, name: str) -> None:
        self.board.set_theme(name)

    def _on_ui_theme(self, name: str) -> None:
        self.ui_theme = UI_THEMES[name]
        preferred = DEFAULT_BOARD_FOR_UI.get(name)
        if preferred and preferred in BOARD_THEMES:
            self.board_theme_box.blockSignals(True)
            self.board_theme_box.setCurrentText(preferred)
            self.board_theme_box.blockSignals(False)
            self.board.set_theme(preferred)
        self._apply_theme()
        self._refresh()

    def _on_difficulty_changed(self, label: str) -> None:
        if not label:
            return
        diff = difficulty_from_label(label)
        self.controller.set_difficulty(diff.key)
        self.diff_desc.setText(diff.description)
        self._refresh(message=f"Difficulty set to {diff.label}.")

    def _on_side_changed(self, side: str) -> None:
        if self._busy():
            color = self.controller.get_player_color()
            self.side_box.blockSignals(True)
            self.side_box.setCurrentText("White" if color is Color.WHITE else "Black")
            self.side_box.blockSignals(False)
            return
        color = Color.WHITE if side == "White" else Color.BLACK
        self.controller.set_player_color(color)
        self.board.set_flipped(color is Color.BLACK)
        self._start_fresh(
            "Playing as White. Your move."
            if color is Color.WHITE
            else "Playing as Black. AI moves first."
        )

    def _on_new_game(self) -> None:
        if self._busy():
            return
        color = self.controller.get_player_color()
        self._start_fresh(
            "New game started. Your move."
            if color is Color.WHITE
            else "New game started. AI moves first."
        )

    def _start_fresh(self, message: str) -> None:
        self.controller.start_new_game()
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        self.last_from = None
        self.last_to = None
        self._refresh(message=message)
        if self.controller.get_state().side_to_move is not self.controller.get_player_color():
            self._start_ai()

    def _on_undo(self) -> None:
        if self._busy():
            return
        if not self.controller.can_undo():
            self._refresh(message="Nothing to undo")
            return
        result = self.controller.undo()
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        history = self.controller.get_move_history()
        if history:
            last = history[-1].move
            self.last_from = last.from_position
            self.last_to = last.to_position
        else:
            self.last_from = None
            self.last_to = None
        self._refresh(message=result.message)

    def _on_copy_pgn(self) -> None:
        QApplication.clipboard().setText(self.controller.to_pgn())
        self._refresh(message="PGN copied to clipboard.")

    def _on_save_pgn(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PGN", "chessmind.pgn", "PGN files (*.pgn)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self.controller.to_pgn())
        except OSError as exc:
            QMessageBox.critical(self, "Save PGN failed", str(exc))
            return
        self._refresh(message=f"PGN saved: {path}")

    def _on_square_clicked(self, clicked: Position) -> None:
        if self._busy():
            return
        state = self.controller.get_state()
        player = self.controller.get_player_color()
        if state.status is not GameStatus.ONGOING:
            return
        if state.side_to_move is not player:
            return

        if self.selected is None:
            piece = state.board.get_piece(clicked)
            if piece is None or piece.color is not player:
                side = "white" if player is Color.WHITE else "black"
                self._refresh(message=f"Select a {side} piece.")
                return
            self._select(clicked)
            return

        if clicked == self.selected:
            self.selected = None
            self.targets.clear()
            self.captures.clear()
            self._refresh(message="Selection cleared.")
            return

        piece = state.board.get_piece(clicked)
        if piece is not None and piece.color is player:
            self._select(clicked)
            return

        source = self.selected
        result = self.controller.make_player_move_from_notation(
            source.to_chess_notation(),
            clicked.to_chess_notation(),
        )
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        if not result.success:
            self._refresh(message=result.message)
            return
        self.last_from = source
        self.last_to = clicked
        self._refresh(
            message=f"You played {source.to_chess_notation()}{clicked.to_chess_notation()}."
        )
        self._maybe_ai_or_end()

    def _select(self, clicked: Position) -> None:
        self.selected = clicked
        legal = [
            move
            for move in self.controller.get_legal_moves()
            if move.from_position == clicked
        ]
        self.targets = {move.to_position for move in legal}
        self.captures = {
            move.to_position
            for move in legal
            if move.move_type
            in {MoveType.CAPTURE, MoveType.PROMOTION_CAPTURE, MoveType.EN_PASSANT}
        }
        self._refresh(message=f"Selected {clicked.to_chess_notation()}.")

    def _maybe_ai_or_end(self) -> None:
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            self._game_over()
            return
        if state.side_to_move is not self.controller.get_player_color():
            self._start_ai()

    def _start_ai(self) -> None:
        self._ai_busy = True
        self._set_controls_enabled(False)
        self.ai_badge.setText(" ● AI thinking")
        self._think_dots = 0
        self._think_timer.start(350)
        self._refresh(message="AI thinking... (UI still responsive)")
        self._worker = AiWorker(self.controller)
        self._worker.finished_ok.connect(self._on_ai_ok)
        self._worker.finished_err.connect(self._on_ai_err)
        self._worker.start()

    def _on_think_tick(self) -> None:
        if not self._ai_busy:
            return
        self._think_dots = (self._think_dots + 1) % 4
        dots = "." * self._think_dots
        self.hint.setText(f"AI thinking{dots} (UI still responsive)")

    def _stop_think(self) -> None:
        self._think_timer.stop()
        self.ai_badge.setText("")

    def _on_ai_ok(self, result, search) -> None:
        self._stop_think()
        self._ai_busy = False
        self._set_controls_enabled(True)
        if result is not None and result.success and search and search.best_move is not None:
            move = search.best_move
            self.last_from = move.from_position
            self.last_to = move.to_position
            notation = (
                f"{move.from_position.to_chess_notation()}"
                f"{move.to_position.to_chess_notation()}"
            )
            self._refresh(message=f"AI played {notation}.")
        else:
            message = result.message if result is not None else "AI failed"
            self._refresh(message=message)
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._game_over()

    def _on_ai_err(self, message: str) -> None:
        self._stop_think()
        self._ai_busy = False
        self._set_controls_enabled(True)
        self._refresh(message=f"AI error: {message}")
        QMessageBox.critical(self, "AI error", message)

    def _game_over(self) -> None:
        pretty = format_status(self.controller.get_state().status)
        self._refresh(message=f"Game over: {pretty}")
        QMessageBox.information(self, "Game over", pretty)


def run_gui(depth: int | None = None, difficulty: str = DEFAULT_DIFFICULTY_KEY) -> None:
    key = difficulty
    if depth is not None:
        mapping = {1: "beginner", 2: "medium", 3: "hard", 4: "expert", 5: "expert"}
        key = mapping.get(depth, DEFAULT_DIFFICULTY_KEY)
    app = QApplication.instance() or QApplication(sys.argv)
    window = ChessMainWindow(difficulty_key=key)
    window.show()
    app.exec()
