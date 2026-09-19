"""PySide6 desktop GUI for ChessMind-AB."""

from __future__ import annotations

import sys
from collections.abc import Callable

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.presentation.qt_board import ChessBoardWidget
from chessmind_ab.presentation.themes import (
    BOARD_THEMES,
    DEFAULT_BOARD_FOR_UI,
    UI_THEMES,
    UiTheme,
)
from chessmind_ab.presentation.ui_common import format_status, piece_glyph

_PROMOTION_CHOICES = (
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT,
)


class PromotionDialog(QDialog):
    """Ask the player which piece a promoting pawn should become."""

    def __init__(self, color: Color, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Promote pawn")
        self.setModal(True)
        self._choice: PieceType | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        prompt = QLabel("Choose a piece to promote to:")
        prompt.setWordWrap(True)
        layout.addWidget(prompt)

        row = QHBoxLayout()
        row.setSpacing(8)
        for piece_type in _PROMOTION_CHOICES:
            glyph = piece_glyph(Piece(type=piece_type, color=color))
            button = QPushButton(f"{glyph}\n{piece_type.name.title()}")
            button.setMinimumSize(88, 72)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if piece_type is PieceType.QUEEN:
                button.setDefault(True)
                button.setObjectName("primary")
            button.clicked.connect(
                lambda _checked=False, chosen=piece_type: self._accept(chosen)
            )
            row.addWidget(button)
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self, piece_type: PieceType) -> None:
        self._choice = piece_type
        self.accept()

    @property
    def choice(self) -> PieceType | None:
        return self._choice


class AiWorker(QThread):
    finished_ok = Signal(object, object)
    finished_err = Signal(str)

    def __init__(
        self,
        controller: GameController,
        *,
        difficulty=None,
        push_undo: bool = False,
        engine_api: bool = False,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._difficulty = difficulty
        self._push_undo = push_undo
        self._engine_api = engine_api

    def run(self) -> None:
        try:
            if self._engine_api:
                result = self._controller.make_engine_move(
                    difficulty=self._difficulty,
                    push_undo=self._push_undo,
                )
            else:
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
        self._animating = False
        self._worker: AiWorker | None = None
        self._think_dots = 0
        self._think_timer = QTimer(self)
        self._think_timer.timeout.connect(self._on_think_tick)
        self._match_running = False
        self._match_paused = False
        self._match_step_once = False
        self._thinking_label = "AI"
        self._review_plies: int | None = None
        self._match_delay_timer = QTimer(self)
        self._match_delay_timer.setSingleShot(True)
        self._match_delay_timer.timeout.connect(self._on_match_delay_elapsed)

        self._build()
        self._install_shortcuts()
        self._apply_theme()
        self._apply_mode_visibility()
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

        board_h = self.board.height()

        # Info card — scrollable body + reserved Actions footer (no overlap).
        self.info_card = self._card()
        self.info_card.setFixedWidth(360)
        self.info_card.setFixedHeight(board_h)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(8)

        self.title = QLabel("ChessMind-AB")
        self.title.setObjectName("appTitle")
        self.title.setFont(QFont("Segoe UI", 17, QFont.Weight.DemiBold))
        self.subtitle = QLabel("Player vs AI  ·  Elo modes")
        self.subtitle.setObjectName("appSubtitle")
        info_layout.addWidget(self.title)
        info_layout.addWidget(self.subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 8, 0)
        body_layout.setSpacing(7)

        self._section(body_layout, "GAME")
        self.mode_value = QLabel("")
        self.turn_value = QLabel("White")
        self.turn_value.setObjectName("turnBadge")
        self.status_value = QLabel("Ongoing")
        self.status_value.setObjectName("statusOk")
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
            body_layout.addLayout(self._kv(key, label))

        self.ai_badge = QLabel("")
        self.ai_badge.setObjectName("badge")
        self.ai_badge.setVisible(False)
        body_layout.addWidget(self.ai_badge)

        self._section(body_layout, "SETTINGS")
        self.mode_box = QComboBox()
        self.mode_box.addItem("Player vs AI", "player")
        self.mode_box.addItem("AI vs AI", "ai_vs_ai")
        body_layout.addLayout(self._labeled("Mode", self.mode_box))
        self.mode_box.currentIndexChanged.connect(self._on_mode_changed)

        self.side_box = QComboBox()
        self.side_box.addItems(["White", "Black"])
        self.side_row = self._labeled("Play as", self.side_box)
        body_layout.addLayout(self.side_row)
        self.side_box.currentTextChanged.connect(self._on_side_changed)

        self.seat_box = QComboBox()
        self.seat_box.addItems(["Bottom", "Top"])
        self.seat_row = self._labeled("Sit at", self.seat_box)
        body_layout.addLayout(self.seat_row)
        self.seat_box.currentTextChanged.connect(self._on_seat_changed)

        self.diff_box = QComboBox()
        for diff in DIFFICULTIES.values():
            self.diff_box.addItem(diff.label, diff.key)
        current = get_difficulty(self.controller.get_difficulty().key)
        self.diff_box.setCurrentText(current.label)
        self.diff_row = self._labeled("Difficulty", self.diff_box)
        body_layout.addLayout(self.diff_row)
        self.diff_box.currentTextChanged.connect(self._on_difficulty_changed)

        self.diff_desc = QLabel(current.description)
        self.diff_desc.setObjectName("key")
        self.diff_desc.setWordWrap(True)
        self.diff_desc.setMinimumHeight(36)
        self.diff_desc.setAlignment(Qt.AlignmentFlag.AlignTop)
        body_layout.addWidget(self.diff_desc)

        self.white_diff_box = QComboBox()
        self.black_diff_box = QComboBox()
        for diff in DIFFICULTIES.values():
            self.white_diff_box.addItem(diff.label, diff.key)
            self.black_diff_box.addItem(diff.label, diff.key)
        self.white_diff_box.setCurrentText(current.label)
        self.black_diff_box.setCurrentText(current.label)
        self.white_diff_row = self._labeled("White AI", self.white_diff_box)
        self.black_diff_row = self._labeled("Black AI", self.black_diff_box)
        body_layout.addLayout(self.white_diff_row)
        body_layout.addLayout(self.black_diff_row)

        self.speed_box = QComboBox()
        for label, ms in (
            ("Fast · 0.3s", 300),
            ("Normal · 0.6s", 600),
            ("Slow · 1.0s", 1000),
            ("Very slow · 1.5s", 1500),
        ):
            self.speed_box.addItem(label, ms)
        self.speed_box.setCurrentIndex(1)
        self.speed_row = self._labeled("Speed", self.speed_box)
        body_layout.addLayout(self.speed_row)

        self.match_panel = QWidget()
        match_grid = QGridLayout(self.match_panel)
        match_grid.setContentsMargins(0, 0, 0, 0)
        match_grid.setHorizontalSpacing(8)
        match_grid.setVerticalSpacing(8)
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        self.step_btn = QPushButton("Step")
        self.start_btn.setToolTip("Start or resume the AI vs AI match")
        self.pause_btn.setToolTip("Pause after the current move")
        self.stop_btn.setToolTip("Stop auto-play (keep the current board)")
        self.step_btn.setToolTip("Play exactly one engine move")
        for btn in (self.start_btn, self.pause_btn, self.stop_btn, self.step_btn):
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        match_grid.addWidget(self.start_btn, 0, 0)
        match_grid.addWidget(self.pause_btn, 0, 1)
        match_grid.addWidget(self.stop_btn, 1, 0)
        match_grid.addWidget(self.step_btn, 1, 1)
        self.start_btn.clicked.connect(self._on_match_start)
        self.pause_btn.clicked.connect(self._on_match_pause)
        self.stop_btn.clicked.connect(self._on_match_stop)
        self.step_btn.clicked.connect(self._on_match_step)
        body_layout.addWidget(self.match_panel)

        self.board_theme_box = QComboBox()
        self.board_theme_box.addItems(list(BOARD_THEMES.keys()))
        body_layout.addLayout(self._labeled("Board", self.board_theme_box))
        self.board_theme_box.currentTextChanged.connect(self._on_board_theme)

        self.ui_theme_box = QComboBox()
        self.ui_theme_box.addItems(list(UI_THEMES.keys()))
        body_layout.addLayout(self._labeled("UI", self.ui_theme_box))
        self.ui_theme_box.currentTextChanged.connect(self._on_ui_theme)
        body_layout.addStretch(1)

        scroll.setWidget(body)
        info_layout.addWidget(scroll, 1)

        self._section(info_layout, "ACTIONS")
        self.new_btn = QPushButton("New Game")
        self.new_btn.setObjectName("primary")
        self.undo_btn = QPushButton("Undo")
        self.copy_btn = QPushButton("Copy PGN")
        self.save_btn = QPushButton("Save PGN")
        self.new_btn.setToolTip("Start a new game (Ctrl+N)")
        self.undo_btn.setToolTip("Undo the last turn (Ctrl+Z)")
        self.copy_btn.setToolTip("Copy the game PGN (Ctrl+C)")
        self.save_btn.setToolTip("Save the game PGN to a file")
        self.new_btn.clicked.connect(self._on_new_game)
        self.undo_btn.clicked.connect(self._on_undo)
        self.copy_btn.clicked.connect(self._on_copy_pgn)
        self.save_btn.clicked.connect(self._on_save_pgn)

        self.actions_panel = QWidget()
        self.actions_panel.setObjectName("actionsPanel")
        self.actions_panel.setMinimumHeight(92)
        self.actions_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        actions = QGridLayout(self.actions_panel)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setHorizontalSpacing(8)
        actions.setVerticalSpacing(8)
        for btn in (self.new_btn, self.undo_btn, self.copy_btn, self.save_btn):
            btn.setFixedHeight(40)
            btn.setMinimumWidth(0)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        actions.addWidget(self.new_btn, 0, 0)
        actions.addWidget(self.undo_btn, 0, 1)
        actions.addWidget(self.copy_btn, 1, 0)
        actions.addWidget(self.save_btn, 1, 1)
        actions.setColumnStretch(0, 1)
        actions.setColumnStretch(1, 1)
        info_layout.addWidget(self.actions_panel, 0)
        layout.addWidget(self.info_card, 0, Qt.AlignmentFlag.AlignTop)

        # History card: two sibling blocks — Move list, then Captured (not nested).
        self.hist_card = self._card()
        self.hist_card.setFixedWidth(310)
        self.hist_card.setFixedHeight(board_h)
        hist_layout = QVBoxLayout(self.hist_card)
        hist_layout.setContentsMargins(12, 12, 12, 12)
        hist_layout.setSpacing(10)

        self.move_panel = QFrame()
        self.move_panel.setObjectName("movePanel")
        move_layout = QVBoxLayout(self.move_panel)
        move_layout.setContentsMargins(10, 10, 10, 10)
        move_layout.setSpacing(8)

        hist_header = QHBoxLayout()
        hist_title_col = QVBoxLayout()
        hist_title = QLabel("MOVE LIST")
        hist_title.setObjectName("section")
        hist_sub = QLabel("Click a row to review")
        hist_sub.setObjectName("key")
        hist_title_col.addWidget(hist_title)
        hist_title_col.addWidget(hist_sub)
        hist_header.addLayout(hist_title_col, 1)
        self.live_btn = QPushButton("Live")
        self.live_btn.setObjectName("liveBtn")
        self.live_btn.setFixedHeight(30)
        self.live_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.live_btn.setToolTip("Return to the live position")
        self.live_btn.clicked.connect(self._on_live_clicked)
        hist_header.addWidget(self.live_btn, 0, Qt.AlignmentFlag.AlignTop)
        move_layout.addLayout(hist_header)

        self.move_header = QLabel(f"{'#':>2}   {'White':<9}{'Black':<9}")
        self.move_header.setObjectName("moveHeader")
        self.move_header.setFont(QFont("Consolas", 11, QFont.Weight.DemiBold))
        move_layout.addWidget(self.move_header)

        self.move_list = QListWidget()
        self.move_list.setFont(QFont("Consolas", 12))
        self.move_list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.move_list.itemClicked.connect(self._on_move_list_clicked)
        move_layout.addWidget(self.move_list, 1)

        self.hint = QLabel("Click your piece, then a marked square.")
        self.hint.setObjectName("hint")
        self.hint.setWordWrap(True)
        self.hint.setFixedHeight(48)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignTop)
        move_layout.addWidget(self.hint)
        hist_layout.addWidget(self.move_panel, 1)

        self.captured_panel = QFrame()
        self.captured_panel.setObjectName("capturedPanel")
        captured_layout = QVBoxLayout(self.captured_panel)
        captured_layout.setContentsMargins(10, 10, 10, 10)
        captured_layout.setSpacing(6)
        captured_title = QLabel("CAPTURED")
        captured_title.setObjectName("section")
        captured_layout.addWidget(captured_title)

        self.captured_you_key = QLabel("YOU")
        self.captured_you_key.setObjectName("capturedKey")
        captured_font = QFont("Segoe UI Symbol", 24, QFont.Weight.DemiBold)
        self.captured_you = QLabel("—")
        self.captured_you.setObjectName("capturedPieces")
        self.captured_you.setFont(captured_font)
        self.captured_you.setWordWrap(True)
        self.captured_you.setMinimumHeight(40)
        self.captured_you.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.captured_ai_key = QLabel("AI")
        self.captured_ai_key.setObjectName("capturedKey")
        self.captured_ai = QLabel("—")
        self.captured_ai.setObjectName("capturedPieces")
        self.captured_ai.setFont(captured_font)
        self.captured_ai.setWordWrap(True)
        self.captured_ai.setMinimumHeight(40)
        self.captured_ai.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        captured_layout.addWidget(self.captured_you_key)
        captured_layout.addWidget(self.captured_you)
        captured_layout.addWidget(self.captured_ai_key)
        captured_layout.addWidget(self.captured_ai)
        hist_layout.addWidget(self.captured_panel, 0)

        layout.addWidget(self.hist_card, 0, Qt.AlignmentFlag.AlignTop)

        self.setFixedSize(self.sizeHint())

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self._on_undo)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._on_new_game)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self._on_copy_pgn)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self._on_escape)

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
                border-radius: 12px;
            }}
            QFrame#movePanel, QFrame#capturedPanel {{
                background: {t.list_bg};
                border: 1px solid {t.input_border};
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; color: {t.text}; }}
            QLabel#appTitle {{
                color: {t.text};
                letter-spacing: 0.2px;
            }}
            QLabel#appSubtitle {{
                color: {t.muted};
                font-size: 12px;
            }}
            QLabel#key, QLabel#section {{ color: {t.muted}; }}
            QLabel#section {{
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.6px;
                margin-top: 6px;
            }}
            QLabel#capturedKey {{
                color: {t.muted};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.4px;
            }}
            QLabel#capturedPieces {{
                color: {t.text};
                font-family: 'Segoe UI Symbol', 'Segoe UI';
                font-size: 28px;
                font-weight: 600;
                letter-spacing: 6px;
                min-height: 40px;
                padding: 4px 0 6px 0;
            }}
            QLabel#moveHeader {{
                color: {t.muted};
                background: {t.list_bg};
                border: 1px solid {t.input_border};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QLabel#hint {{
                color: {t.muted};
                background: {t.list_bg};
                border: 1px solid {t.input_border};
                border-radius: 8px;
                padding: 8px;
            }}
            QLabel#badge {{
                color: {t.accent};
                background: {t.accent_soft};
                padding: 6px 8px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QLabel#turnBadge {{
                color: {t.accent};
                font-weight: 700;
            }}
            QLabel#statusOk {{
                color: #3ecf8e;
                font-weight: 600;
            }}
            QLabel#statusEnd {{
                color: #ff7b72;
                font-weight: 700;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QComboBox, QListWidget {{
                background: {t.input_bg};
                color: {t.text};
                border: 1px solid {t.input_border};
                padding: 6px 8px;
                border-radius: 8px;
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
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {t.button_hover};
                border-color: {t.accent};
            }}
            QPushButton:pressed {{
                background: {t.accent_soft};
            }}
            QPushButton:focus {{
                border: 1px solid {t.accent};
            }}
            QPushButton:disabled {{
                color: {t.muted};
                background: {t.list_bg};
            }}
            QPushButton#primary {{
                background: {t.accent};
                color: #ffffff;
                border: 1px solid {t.accent};
            }}
            QPushButton#primary:hover {{
                background: {t.button_hover};
                border-color: {t.accent};
                color: {t.text};
            }}
            QPushButton#primary:disabled {{
                color: {t.muted};
                background: {t.list_bg};
                border-color: {t.input_border};
            }}
            QPushButton#liveBtn {{
                padding: 4px 10px;
                font-size: 12px;
                min-width: 52px;
            }}
            QListWidget {{
                background: {t.list_bg};
                outline: none;
                border-radius: 8px;
            }}
            QListWidget::item {{
                padding: 5px 7px;
                color: {t.text};
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background: {t.accent_soft};
            }}
            QListWidget::item:selected {{
                background: {t.accent};
                color: #ffffff;
            }}
            """
        )
        self.board.update()

    def _busy(self) -> bool:
        return self._ai_busy or self._animating

    def _is_ai_vs_ai(self) -> bool:
        return self.mode_box.currentData() == "ai_vs_ai"

    def _set_layout_visible(self, layout: QHBoxLayout, visible: bool) -> None:
        for index in range(layout.count()):
            item = layout.itemAt(index)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setVisible(visible)

    def _apply_mode_visibility(self) -> None:
        ai_match = self._is_ai_vs_ai()
        self._set_layout_visible(self.side_row, not ai_match)
        self._set_layout_visible(self.seat_row, not ai_match)
        self._set_layout_visible(self.diff_row, not ai_match)
        self.diff_desc.setVisible(not ai_match)
        self._set_layout_visible(self.white_diff_row, ai_match)
        self._set_layout_visible(self.black_diff_row, ai_match)
        self._set_layout_visible(self.speed_row, ai_match)
        self.match_panel.setVisible(ai_match)
        self._update_match_controls()

    def _match_delay_ms(self) -> int:
        data = self.speed_box.currentData()
        return int(data) if data is not None else 600

    def _difficulty_for_side(self, color: Color):
        if not self._is_ai_vs_ai():
            return self.controller.get_difficulty()
        box = self.white_diff_box if color is Color.WHITE else self.black_diff_box
        key = box.currentData() or self.controller.get_difficulty().key
        return get_difficulty(key)

    def _update_match_controls(self) -> None:
        ai_match = self._is_ai_vs_ai()
        idle = not self._busy()
        ongoing = self.controller.get_state().status is GameStatus.ONGOING
        self.start_btn.setEnabled(
            ai_match and idle and ongoing and (not self._match_running or self._match_paused)
        )
        self.pause_btn.setEnabled(ai_match and self._match_running and not self._match_paused)
        self.stop_btn.setEnabled(
            ai_match and (self._match_running or self._match_paused or self._match_step_once)
        )
        self.step_btn.setEnabled(ai_match and idle and ongoing and not self._match_running)
        self.mode_box.setEnabled(idle and not self._match_running)
        self.white_diff_box.setEnabled(idle and not self._match_running)
        self.black_diff_box.setEnabled(idle and not self._match_running)
        self.speed_box.setEnabled(ai_match)

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self.mode_box,
            self.side_box,
            self.seat_box,
            self.diff_box,
            self.white_diff_box,
            self.black_diff_box,
            self.speed_box,
            self.board_theme_box,
            self.ui_theme_box,
            self.new_btn,
            self.undo_btn,
            self.copy_btn,
            self.save_btn,
        ):
            widget.setEnabled(enabled)
        # New Game must stay available while the engine is thinking.
        self.new_btn.setEnabled(True)
        if enabled and not self._busy():
            self.undo_btn.setEnabled(self.controller.can_undo())
            self._update_match_controls()
        elif not enabled:
            for btn in (self.start_btn, self.pause_btn, self.stop_btn, self.step_btn):
                btn.setEnabled(False)

    def _extra_slides_for_move(
        self, move: Move
    ) -> list[tuple[Piece, Position, Position]]:
        path = StateTransition.castling_rook_path(move)
        if path is None:
            return []
        rook_from, rook_to = path
        rook = self.controller.get_state().board.get_piece(rook_to)
        if rook is None:
            return []
        return [(rook, rook_from, rook_to)]

    def _animate_then(
        self,
        piece: Piece,
        from_pos: Position,
        to_pos: Position,
        *,
        message: str,
        after: Callable[[], None] | None = None,
        extra_slides: list[tuple[Piece, Position, Position]] | None = None,
    ) -> None:
        extras = list(extra_slides or [])
        self._animating = True
        self._set_controls_enabled(False)
        # Allow bailing out mid-slide without waiting for AI.
        self.new_btn.setEnabled(True)
        self.undo_btn.setEnabled(self.controller.can_undo())
        self.last_from = from_pos
        self.last_to = to_pos
        # Avoid a one-frame flash of pieces already on destinations.
        hidden = {from_pos, to_pos}
        for _, src, dst in extras:
            hidden.add(src)
            hidden.add(dst)
        self.board.hidden = hidden
        self._refresh(message=message)

        def _done() -> None:
            self._animating = False
            self._refresh(message=message)
            if after is not None:
                after()
            if not self._ai_busy:
                self._set_controls_enabled(True)

        self.board.animate_move(
            piece,
            from_pos,
            to_pos,
            on_finished=_done,
            extra_slides=extras or None,
        )

    def _checked_square(self, state=None) -> Position | None:
        return self.controller.checked_king_position(state)

    def _format_captured(self, pieces: list[Piece]) -> str:
        if not pieces:
            return "—"
        ordered = sorted(pieces, key=material_sort_key)
        # Thin spaces keep glyphs readable at large size without crowding.
        return "\u2009".join(piece_glyph(piece) for piece in ordered)

    def _is_reviewing(self) -> bool:
        return self._review_plies is not None

    def _exit_review(self) -> None:
        self._review_plies = None

    def _refresh(self, message: str | None = None) -> None:
        live_state = self.controller.get_state()
        history = self.controller.get_move_history()
        if self._review_plies is not None and self._review_plies > len(history):
            self._review_plies = len(history) if history else None

        reviewing = self._is_reviewing()
        state = (
            self.controller.state_after_plies(self._review_plies)
            if reviewing
            else live_state
        )
        diff = self.controller.get_difficulty()
        if self._is_ai_vs_ai():
            white = self._difficulty_for_side(Color.WHITE)
            black = self._difficulty_for_side(Color.BLACK)
            self.mode_value.setText(f"AI vs AI · {white.name}/{black.name}")
            self.subtitle.setText("Spectator mode  ·  dual Elo engines")
        else:
            self.mode_value.setText(diff.label)
            side = "White" if self.controller.get_player_color() is Color.WHITE else "Black"
            self.subtitle.setText(f"Player vs AI  ·  playing as {side}")

        self.turn_value.setText(
            "White" if state.side_to_move is Color.WHITE else "Black"
        )
        self.status_value.setText(format_status(state.status))
        self.status_value.setObjectName(
            "statusOk" if state.status is GameStatus.ONGOING else "statusEnd"
        )
        self.status_value.style().unpolish(self.status_value)
        self.status_value.style().polish(self.status_value)

        if reviewing and self._review_plies:
            self.last_value.setText(history[self._review_plies - 1].notation)
        else:
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

        if self._is_ai_vs_ai():
            self.captured_you_key.setText("WHITE")
            self.captured_ai_key.setText("BLACK")
            self.captured_you.setText(
                self._format_captured(
                    self.controller.get_captured_pieces(Color.WHITE)
                )
            )
            self.captured_ai.setText(
                self._format_captured(
                    self.controller.get_captured_pieces(Color.BLACK)
                )
            )
        else:
            player = self.controller.get_player_color()
            self.captured_you_key.setText("YOU")
            self.captured_ai_key.setText("AI")
            self.captured_you.setText(
                self._format_captured(self.controller.get_captured_pieces(player))
            )
            self.captured_ai.setText(
                self._format_captured(
                    self.controller.get_captured_pieces(player.opposite())
                )
            )

        selected_row = -1
        self.move_list.blockSignals(True)
        self.move_list.clear()
        for index in range(0, len(history), 2):
            white = history[index].notation
            black = history[index + 1].notation if index + 1 < len(history) else ""
            text = f"{index // 2 + 1:>2}. {white:<9}{black:<9}"
            item = QListWidgetItem(text)
            if (index // 2) % 2 == 1:
                item.setBackground(QColor(self.ui_theme.row_alt))
            end_plies = index + 2 if index + 1 < len(history) else index + 1
            item.setData(Qt.ItemDataRole.UserRole, end_plies)
            self.move_list.addItem(item)
            if reviewing and self._review_plies == end_plies:
                selected_row = index // 2
        if reviewing and selected_row >= 0:
            self.move_list.setCurrentRow(selected_row)
        elif not reviewing and history:
            self.move_list.scrollToBottom()
        self.move_list.blockSignals(False)

        self.live_btn.setEnabled(reviewing and not self._busy())
        self.undo_btn.setEnabled(
            self.controller.can_undo() and not self._ai_busy and not reviewing
        )
        if message is not None:
            self.hint.setText(message)
        elif reviewing:
            self.hint.setText(
                f"Reviewing after ply {self._review_plies}. "
                "Press Live or select the latest row to return."
            )

        if reviewing:
            last_from = last_to = None
            if self._review_plies and self._review_plies <= len(history):
                last = history[self._review_plies - 1].move
                last_from = last.from_position
                last_to = last.to_position
            self.board.sync(
                state,
                selected=None,
                targets=set(),
                captures=set(),
                last_from=last_from,
                last_to=last_to,
                checked=self._checked_square(state),
            )
        else:
            self.board.sync(
                state,
                selected=self.selected,
                targets=self.targets,
                captures=self.captures,
                last_from=self.last_from,
                last_to=self.last_to,
                checked=self._checked_square(state),
            )
        self._update_match_controls()

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
        if not label or self._is_ai_vs_ai():
            return
        diff = difficulty_from_label(label)
        self.controller.set_difficulty(diff.key)
        self.diff_desc.setText(diff.description)
        self._refresh(message=f"Difficulty set to {diff.label}.")

    def _on_mode_changed(self) -> None:
        if self._busy() or self._match_running:
            return
        self._stop_match_timers()
        self._match_running = False
        self._match_paused = False
        self._match_step_once = False
        if self._is_ai_vs_ai():
            self.controller.set_player_color(Color.WHITE)
            self.side_box.blockSignals(True)
            self.side_box.setCurrentText("White")
            self.side_box.blockSignals(False)
            self._apply_mode_visibility()
            self._reset_game_and_turn_board(
                False, "AI vs AI ready. Press Start or Step.", auto_ai=False
            )
        else:
            self._apply_mode_visibility()
            color = self.controller.get_player_color()
            self._reset_game_and_turn_board(
                self._want_flipped(),
                "Player vs AI. Your move."
                if color is Color.WHITE
                else "Player vs AI. AI moves first.",
                auto_ai=True,
            )

    def _seat_is_top(self) -> bool:
        return self.seat_box.currentText() == "Top"

    def _want_flipped(self) -> bool:
        """Black at the bottom of the widget (180 degree view)."""
        playing_black = self.controller.get_player_color() is Color.BLACK
        return playing_black != self._seat_is_top()

    def _on_side_changed(self, side: str) -> None:
        if self._is_ai_vs_ai():
            color = self.controller.get_player_color()
            self.side_box.blockSignals(True)
            self.side_box.setCurrentText("White" if color is Color.WHITE else "Black")
            self.side_box.blockSignals(False)
            return
        color = Color.WHITE if side == "White" else Color.BLACK
        self.controller.set_player_color(color)
        self._reset_game_and_turn_board(
            self._want_flipped(),
            "Playing as White. Your move."
            if color is Color.WHITE
            else "Playing as Black. AI moves first.",
            auto_ai=True,
        )

    def _on_seat_changed(self, seat: str) -> None:
        if self._is_ai_vs_ai() or self._busy():
            playing_black = self.controller.get_player_color() is Color.BLACK
            shown_top = playing_black != self.board.geometry_helper.flipped
            self.seat_box.blockSignals(True)
            self.seat_box.setCurrentText("Top" if shown_top else "Bottom")
            self.seat_box.blockSignals(False)
            return
        if seat not in {"Top", "Bottom"}:
            return
        where = "top" if self._seat_is_top() else "bottom"
        self._turn_board_in_place(f"You sit at the {where}.")

    def _turn_board_in_place(self, message: str) -> None:
        """Rotate the current game to the selected seat. Does not start a new game."""
        want = self._want_flipped()
        if self.board.geometry_helper.flipped is want:
            self._refresh(message=message)
            return
        self._set_controls_enabled(False)
        self.new_btn.setEnabled(True)
        self._refresh(message="Turning the board...")
        self._animating = True

        def _done() -> None:
            self._animating = False
            self._set_controls_enabled(True)
            self._refresh(message=message)

        self.board.animate_viewpoint_flip(want, on_finished=_done)

    def _reset_game_and_turn_board(
        self, want_flipped: bool, message: str, *, auto_ai: bool
    ) -> None:
        """New game, then rotate the board 180 degrees if the seat changed."""
        self._abort_worker()
        self.board.cancel_animation(run_callback=False)
        self._animating = False
        self._exit_review()
        self.controller.start_new_game()
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        self.last_from = None
        self.last_to = None
        if self.board.geometry_helper.flipped is want_flipped:
            self._set_controls_enabled(True)
            self._refresh(message=message)
            if (
                auto_ai
                and not self._is_ai_vs_ai()
                and self.controller.get_state().side_to_move
                is not self.controller.get_player_color()
            ):
                self._start_ai()
            return

        self._set_controls_enabled(False)
        self.new_btn.setEnabled(True)
        self._refresh(message="Turning the board...")
        self._animating = True

        def _done() -> None:
            self._animating = False
            self._set_controls_enabled(True)
            self._refresh(message=message)
            if (
                auto_ai
                and not self._is_ai_vs_ai()
                and self.controller.get_state().side_to_move
                is not self.controller.get_player_color()
            ):
                self._start_ai()

        self.board.animate_viewpoint_flip(want_flipped, on_finished=_done)

    def _abort_worker(self) -> None:
        worker = self._worker
        if worker is not None and worker.isRunning():
            try:
                worker.finished_ok.disconnect()
                worker.finished_err.disconnect()
            except RuntimeError:
                pass
            self.controller.cancel_search()
            worker.wait(8000)
        self._stop_think()
        self._ai_busy = False
        self._worker = None

    def _on_new_game(self) -> None:
        self._abort_worker()
        self._stop_match_timers()
        self._match_running = False
        self._match_paused = False
        self._match_step_once = False
        self._exit_review()
        if self._is_ai_vs_ai():
            self.board.set_flipped(False)
            self._start_fresh("New AI vs AI game. Press Start or Step.", auto_ai=False)
            return
        color = self.controller.get_player_color()
        self._start_fresh(
            "New game started. Your move."
            if color is Color.WHITE
            else "New game started. AI moves first."
        )

    def _start_fresh(self, message: str, *, auto_ai: bool = True) -> None:
        self.board.cancel_animation(run_callback=False)
        self._animating = False
        self._exit_review()
        self.controller.start_new_game()
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        self.last_from = None
        self.last_to = None
        self._set_controls_enabled(True)
        self._refresh(message=message)
        if (
            auto_ai
            and not self._is_ai_vs_ai()
            and self.controller.get_state().side_to_move
            is not self.controller.get_player_color()
        ):
            self._start_ai()

    def _stop_match_timers(self) -> None:
        self._match_delay_timer.stop()

    def _on_match_start(self) -> None:
        if not self._is_ai_vs_ai() or self._busy():
            return
        if self.controller.get_state().status is not GameStatus.ONGOING:
            return
        self._match_running = True
        self._match_paused = False
        self._match_step_once = False
        self._refresh(message="AI vs AI running...")
        self._start_engine_turn()

    def _on_match_pause(self) -> None:
        if not self._is_ai_vs_ai():
            return
        self._match_paused = True
        self._stop_match_timers()
        self._refresh(message="AI vs AI paused.")

    def _on_match_stop(self) -> None:
        if not self._is_ai_vs_ai():
            return
        self._abort_worker()
        self._match_running = False
        self._match_paused = False
        self._match_step_once = False
        self._stop_match_timers()
        self._set_controls_enabled(True)
        self._refresh(message="AI vs AI stopped.")

    def _on_match_step(self) -> None:
        if not self._is_ai_vs_ai() or self._busy():
            return
        if self.controller.get_state().status is not GameStatus.ONGOING:
            return
        self._match_running = False
        self._match_paused = True
        self._match_step_once = True
        self._stop_match_timers()
        self._refresh(message="Stepping one engine move...")
        self._start_engine_turn()

    def _on_match_delay_elapsed(self) -> None:
        if not self._is_ai_vs_ai():
            return
        if not self._match_running or self._match_paused or self._busy():
            return
        if self.controller.get_state().status is not GameStatus.ONGOING:
            return
        self._start_engine_turn()

    def _schedule_next_match_turn(self) -> None:
        if not self._is_ai_vs_ai():
            return
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._match_running = False
            self._match_paused = False
            self._match_step_once = False
            self._game_over()
            return
        if self._match_step_once:
            self._match_step_once = False
            self._match_paused = True
            self._match_running = False
            self._refresh(message="Step done. Press Start or Step.")
            return
        if self._match_running and not self._match_paused:
            self._match_delay_timer.start(self._match_delay_ms())
            self._refresh(message="AI vs AI running...")
        else:
            self._update_match_controls()

    def _pgn_text(self) -> str:
        if self._is_ai_vs_ai():
            white = f"AI ({self._difficulty_for_side(Color.WHITE).label})"
            black = f"AI ({self._difficulty_for_side(Color.BLACK).label})"
            return self.controller.to_pgn(white=white, black=black)
        return self.controller.to_pgn()

    def _on_escape(self) -> None:
        if self._busy():
            return
        if self._is_reviewing():
            self._on_live_clicked()
            return
        if self.selected is not None:
            self.selected = None
            self.targets.clear()
            self.captures.clear()
            self._refresh(message="Selection cleared.")

    def _on_live_clicked(self) -> None:
        self._exit_review()
        self._refresh(message="Back to live position.")

    def _on_move_list_clicked(self, item: QListWidgetItem) -> None:
        if self._busy():
            return
        plies = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(plies, int) or plies <= 0:
            return
        history = self.controller.get_move_history()
        if plies >= len(history):
            self._exit_review()
            self._refresh(message="Live position.")
            return
        self._review_plies = plies
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        self._refresh()

    def _on_undo(self) -> None:
        if self._ai_busy:
            return
        if self._is_ai_vs_ai() and self._match_running and not self._match_paused:
            self._on_match_pause()
        if not self.controller.can_undo():
            self._refresh(message="Nothing to undo")
            return
        self.board.cancel_animation(run_callback=False)
        self._animating = False
        self._exit_review()
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
        QApplication.clipboard().setText(self._pgn_text())
        self._refresh(message="PGN copied to clipboard.")

    def _on_save_pgn(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PGN", "chessmind.pgn", "PGN files (*.pgn)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self._pgn_text())
        except OSError as exc:
            QMessageBox.critical(self, "Save PGN failed", str(exc))
            return
        self._refresh(message=f"PGN saved: {path}")

    def _on_square_clicked(self, clicked: Position) -> None:
        if self._busy() or self._is_ai_vs_ai() or self._is_reviewing():
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
        moving = state.board.get_piece(source)
        from_sq = source.to_chess_notation()
        to_sq = clicked.to_chess_notation()
        candidates = self.controller.find_move_candidates(from_sq, to_sq)
        promotion: PieceType | None = None
        if any(move.promotion_piece is not None for move in candidates):
            promotion = self._ask_promotion_piece(player)
            if promotion is None:
                self._refresh(message="Promotion cancelled.")
                return

        self._exit_review()
        result = self.controller.make_player_move_from_notation(
            from_sq,
            to_sq,
            promotion=promotion,
        )
        self.selected = None
        self.targets.clear()
        self.captures.clear()
        if not result.success:
            self._refresh(message=result.message)
            return
        message = f"You played {from_sq}{to_sq}."
        if promotion is not None:
            message = f"You played {from_sq}{to_sq}={promotion.name[0]}."
        history = self.controller.get_move_history()
        last_move = history[-1].move if history else None
        extras = self._extra_slides_for_move(last_move) if last_move is not None else []
        # Prefer the piece now on the destination (promoted piece after promote).
        animated = self.controller.get_state().board.get_piece(clicked) or moving
        if animated is None:
            self.last_from = source
            self.last_to = clicked
            self._refresh(message=message)
            self._maybe_ai_or_end()
            return
        self._animate_then(
            animated,
            source,
            clicked,
            message=message,
            after=self._maybe_ai_or_end,
            extra_slides=extras,
        )

    def _ask_promotion_piece(self, color: Color) -> PieceType | None:
        dialog = PromotionDialog(color, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.choice

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
        if self._is_ai_vs_ai():
            return
        if state.side_to_move is not self.controller.get_player_color():
            self._start_ai()

    def _start_ai(self) -> None:
        self._start_engine_turn(player_vs_ai=True)

    def _start_engine_turn(self, *, player_vs_ai: bool | None = None) -> None:
        if self._busy():
            return
        if self.controller.get_state().status is not GameStatus.ONGOING:
            return
        use_pva = (
            (not self._is_ai_vs_ai())
            if player_vs_ai is None
            else player_vs_ai
        )
        side = self.controller.get_state().side_to_move
        difficulty = None if use_pva else self._difficulty_for_side(side)
        self._ai_busy = True
        self._set_controls_enabled(False)
        if use_pva:
            self._thinking_label = "AI"
        else:
            self._thinking_label = (
                "White AI" if side is Color.WHITE else "Black AI"
            )
        badge = f" ● {self._thinking_label} thinking"
        hint = f"{self._thinking_label} thinking... (UI still responsive)"
        self.ai_badge.setText(badge)
        self.ai_badge.setVisible(True)
        self._think_dots = 0
        self._think_timer.start(350)
        self._refresh(message=hint)
        self._worker = AiWorker(
            self.controller,
            difficulty=difficulty,
            push_undo=not use_pva,
            engine_api=not use_pva,
        )
        self._worker.finished_ok.connect(self._on_ai_ok)
        self._worker.finished_err.connect(self._on_ai_err)
        self._worker.start()

    def _on_think_tick(self) -> None:
        if not self._ai_busy:
            return
        self._think_dots = (self._think_dots + 1) % 4
        dots = "." * self._think_dots
        self.hint.setText(
            f"{self._thinking_label} thinking{dots} (UI still responsive)"
        )

    def _stop_think(self) -> None:
        self._think_timer.stop()
        self.ai_badge.setText("")
        self.ai_badge.setVisible(False)

    def _on_ai_ok(self, result, search) -> None:
        self._stop_think()
        self._ai_busy = False
        if result is not None and result.success and search and search.best_move is not None:
            move = search.best_move
            notation = (
                f"{move.from_position.to_chess_notation()}"
                f"{move.to_position.to_chess_notation()}"
            )
            if self._is_ai_vs_ai():
                # Side has already flipped after the move was applied.
                mover = move.moving_piece.color
                who = "White AI" if mover is Color.WHITE else "Black AI"
                message = f"{who} played {notation}."
            else:
                message = f"AI played {notation}."
            piece = self.controller.get_state().board.get_piece(move.to_position)
            if piece is None:
                self.last_from = move.from_position
                self.last_to = move.to_position
                self._set_controls_enabled(True)
                self._refresh(message=message)
                if self._is_ai_vs_ai():
                    self._schedule_next_match_turn()
                elif self.controller.get_state().status is not GameStatus.ONGOING:
                    self._game_over()
                return

            def _after_ai_anim() -> None:
                if self._is_ai_vs_ai():
                    self._schedule_next_match_turn()
                elif self.controller.get_state().status is not GameStatus.ONGOING:
                    self._game_over()

            self._animate_then(
                piece,
                move.from_position,
                move.to_position,
                message=message,
                after=_after_ai_anim,
                extra_slides=self._extra_slides_for_move(move),
            )
            return

        message = result.message if result is not None else "AI failed"
        self._set_controls_enabled(True)
        self._refresh(message=message)
        if self._is_ai_vs_ai():
            self._match_running = False
            self._match_step_once = False
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._game_over()

    def _on_ai_err(self, message: str) -> None:
        self._stop_think()
        self._ai_busy = False
        self._animating = False
        self._match_running = False
        self._match_step_once = False
        self._stop_match_timers()
        self.board.cancel_animation(run_callback=False)
        self._set_controls_enabled(True)
        self._refresh(message=f"AI error: {message}")
        QMessageBox.critical(self, "AI error", message)

    def _game_over(self) -> None:
        self._match_running = False
        self._match_paused = False
        self._match_step_once = False
        self._stop_match_timers()
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
