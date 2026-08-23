"""Tkinter GUI: Elo difficulty modes, move animation, polished panel."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import InvalidPositionError, Position
from chessmind_ab.presentation.board_geometry import BoardGeometry
from chessmind_ab.presentation.piece_images import PieceImageCache
from chessmind_ab.presentation.themes import BOARD_THEMES, UI_THEMES, BoardTheme, UiTheme

_PIECE_GLYPHS = {
    (PieceType.KING, Color.WHITE): "♔",
    (PieceType.QUEEN, Color.WHITE): "♕",
    (PieceType.ROOK, Color.WHITE): "♖",
    (PieceType.BISHOP, Color.WHITE): "♗",
    (PieceType.KNIGHT, Color.WHITE): "♘",
    (PieceType.PAWN, Color.WHITE): "♙",
    (PieceType.KING, Color.BLACK): "♚",
    (PieceType.QUEEN, Color.BLACK): "♛",
    (PieceType.ROOK, Color.BLACK): "♜",
    (PieceType.BISHOP, Color.BLACK): "♝",
    (PieceType.KNIGHT, Color.BLACK): "♞",
    (PieceType.PAWN, Color.BLACK): "♟",
}

_ANIM_STEPS = 12
_ANIM_INTERVAL_MS = 16


def piece_glyph(piece: Piece) -> str:
    return _PIECE_GLYPHS[(piece.type, piece.color)]


def format_status(status: GameStatus) -> str:
    return status.name.replace("_", " ").title()


class ChessGuiApp:
    def __init__(
        self,
        root: tk.Tk,
        difficulty_key: str = DEFAULT_DIFFICULTY_KEY,
    ) -> None:
        self.root = root
        self.root.title("ChessMind-AB")
        self.root.resizable(False, False)

        self.board_theme: BoardTheme = BOARD_THEMES["green"]
        self.ui_theme: UiTheme = UI_THEMES["dark"]

        self.geometry = BoardGeometry(square_size=88, margin=36)
        self.piece_images = PieceImageCache(self.geometry.square_size)
        self.controller = GameController(
            difficulty_key=difficulty_key, player_color=Color.WHITE
        )
        self.controller.start_new_game()

        self.selected: Position | None = None
        self.target_squares: set[Position] = set()
        self.capture_targets: set[Position] = set()
        self.last_from: Position | None = None
        self.last_to: Position | None = None
        self._flash_to: Position | None = None
        self._ai_busy = False
        self._animating = False
        self._hover: Position | None = None
        self._hidden_positions: set[Position] = set()
        self._floating: dict[str, object] = {}
        self._think_job: object | None = None
        self._think_dots = 0

        self._build_layout()
        self._apply_theme_styles()
        self._redraw()
        self._refresh_panel()

    def _build_layout(self) -> None:
        self._style = ttk.Style(self.root)
        try:
            self._style.theme_use("clam")
        except tk.TclError:
            pass
        self._style.configure("Panel.TButton", padding=(10, 6))
        self._style.configure("Panel.TCombobox", padding=4)

        self.shell = tk.Frame(self.root, bg=self.ui_theme.app_bg, padx=16, pady=16)
        self.shell.grid(row=0, column=0, sticky="nsew")

        board_wrap = tk.Frame(self.shell, bg=self.ui_theme.app_bg)
        board_wrap.grid(row=0, column=0, sticky="n")

        size = self.geometry.board_pixels + self.geometry.margin * 2
        self.canvas = tk.Canvas(
            board_wrap,
            width=size,
            height=size,
            background=self.board_theme.canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

        self._theme_surfaces: list[tk.Misc] = []
        self._section_labels: list[tk.Label] = []
        self._key_labels: list[tk.Label] = []
        self._value_labels: list[tk.Label] = []
        self._card_borders: list[tk.Frame] = []

        # Column 2: game info / controls (card)
        self.panel_border, self.panel = self._make_card(self.shell, width=312)
        self.panel_border.grid(row=0, column=1, sticky="ns", padx=(16, 0))
        self.panel_border.configure(height=size)
        self.panel_border.grid_propagate(False)

        # Column 3: history (card)
        self.history_border, self.history_panel = self._make_card(self.shell, width=292)
        self.history_border.grid(row=0, column=2, sticky="ns", padx=(12, 0))
        self.history_border.configure(height=size)
        self.history_border.grid_propagate(False)

        self.title_label = tk.Label(
            self.panel,
            text="ChessMind-AB",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI Semibold", 16),
            anchor="w",
        )
        self.title_label.pack(fill="x")
        self.subtitle_label = tk.Label(
            self.panel,
            text="White vs AI  ·  Elo modes",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(0, 10))

        self.turn_var = tk.StringVar(value="White")
        self.status_var = tk.StringVar(value="Ongoing")
        self.mode_var = tk.StringVar(value="")
        self.last_move_var = tk.StringVar(value="—")
        self.ai_info_var = tk.StringVar(value="waiting")
        self.stats_var = tk.StringVar(value="—")
        self.hint_var = tk.StringVar(value="Click a white piece, then a marked square.")
        self.captured_white_var = tk.StringVar(value="—")
        self.captured_black_var = tk.StringVar(value="—")

        self._add_section(self.panel, "Game")
        for key, var in (
            ("Mode", self.mode_var),
            ("Turn", self.turn_var),
            ("Status", self.status_var),
            ("Last", self.last_move_var),
            ("AI", self.ai_info_var),
            ("Stats", self.stats_var),
        ):
            self._add_kv_row(self.panel, key, var)

        self.ai_badge = tk.Label(
            self.panel,
            text="",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.accent,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        )
        self.ai_badge.pack(fill="x", pady=(4, 0))

        captured_box = tk.Frame(self.panel, bg=self.ui_theme.card_bg, height=44)
        captured_box.pack(fill="x", pady=(8, 0))
        captured_box.pack_propagate(False)
        self._theme_surfaces.append(captured_box)
        self.captured_white_label = tk.Label(
            captured_box,
            textvariable=self.captured_white_var,
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.captured_white_label.pack(fill="x")
        self.captured_black_label = tk.Label(
            captured_box,
            textvariable=self.captured_black_var,
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.captured_black_label.pack(fill="x")
        self._value_labels.extend([self.captured_white_label, self.captured_black_label])

        self._add_section(self.panel, "Settings")

        diff_row = tk.Frame(self.panel, bg=self.ui_theme.card_bg)
        diff_row.pack(fill="x", pady=(0, 6))
        self._theme_surfaces.append(diff_row)
        diff_key = tk.Label(
            diff_row,
            text="Difficulty",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
        )
        diff_key.pack(side=tk.LEFT)
        self._key_labels.append(diff_key)
        current = self.controller.get_difficulty()
        self.difficulty_var = tk.StringVar(value=current.label)
        self.difficulty_box = ttk.Combobox(
            diff_row,
            textvariable=self.difficulty_var,
            values=[d.label for d in DIFFICULTIES.values()],
            width=22,
            state="readonly",
            style="Panel.TCombobox",
        )
        self.difficulty_box.pack(side=tk.RIGHT)
        self.difficulty_var.trace_add("write", lambda *_: self._on_difficulty_changed())

        # Fixed-height description so changing difficulty never reflows the card.
        desc_box = tk.Frame(self.panel, bg=self.ui_theme.card_bg, height=40)
        desc_box.pack(fill="x", pady=(0, 8))
        desc_box.pack_propagate(False)
        self._theme_surfaces.append(desc_box)
        self.difficulty_desc = tk.Label(
            desc_box,
            text=current.description,
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
            anchor="nw",
            justify="left",
            wraplength=270,
        )
        self.difficulty_desc.pack(fill="both", expand=True)

        theme_row = tk.Frame(self.panel, bg=self.ui_theme.card_bg)
        theme_row.pack(fill="x", pady=(0, 6))
        self._theme_surfaces.append(theme_row)
        board_key = tk.Label(
            theme_row,
            text="Board",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
        )
        board_key.pack(side=tk.LEFT)
        self._key_labels.append(board_key)
        self.board_theme_var = tk.StringVar(value="green")
        ttk.Combobox(
            theme_row,
            textvariable=self.board_theme_var,
            values=list(BOARD_THEMES.keys()),
            width=10,
            state="readonly",
            style="Panel.TCombobox",
        ).pack(side=tk.RIGHT)
        self.board_theme_var.trace_add("write", lambda *_: self._on_theme_changed())

        ui_row = tk.Frame(self.panel, bg=self.ui_theme.card_bg)
        ui_row.pack(fill="x", pady=(0, 4))
        self._theme_surfaces.append(ui_row)
        ui_key = tk.Label(
            ui_row,
            text="UI",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
        )
        ui_key.pack(side=tk.LEFT)
        self._key_labels.append(ui_key)
        self.ui_theme_var = tk.StringVar(value="dark")
        ttk.Combobox(
            ui_row,
            textvariable=self.ui_theme_var,
            values=list(UI_THEMES.keys()),
            width=10,
            state="readonly",
            style="Panel.TCombobox",
        ).pack(side=tk.RIGHT)
        self.ui_theme_var.trace_add("write", lambda *_: self._on_theme_changed())

        self._add_section(self.panel, "Actions")
        btn_row = tk.Frame(self.panel, bg=self.ui_theme.card_bg)
        btn_row.pack(fill="x", pady=(0, 6))
        self._theme_surfaces.append(btn_row)
        ttk.Button(
            btn_row, text="New Game", style="Panel.TButton", command=self._on_new_game
        ).pack(side=tk.LEFT, expand=True, fill="x", padx=(0, 4))
        self.undo_btn = ttk.Button(
            btn_row, text="Undo", style="Panel.TButton", command=self._on_undo
        )
        self.undo_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=(4, 0))

        pgn_row = tk.Frame(self.panel, bg=self.ui_theme.card_bg)
        pgn_row.pack(fill="x")
        self._theme_surfaces.append(pgn_row)
        ttk.Button(
            pgn_row, text="Copy PGN", style="Panel.TButton", command=self._on_copy_pgn
        ).pack(side=tk.LEFT, expand=True, fill="x", padx=(0, 4))
        ttk.Button(
            pgn_row, text="Save PGN", style="Panel.TButton", command=self._on_save_pgn
        ).pack(side=tk.LEFT, expand=True, fill="x", padx=(4, 0))

        # History column
        self.move_list_title = tk.Label(
            self.history_panel,
            text="Move list",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI Semibold", 11),
            anchor="w",
        )
        self.move_list_title.pack(fill="x", pady=(0, 2))
        self.move_list_subtitle = tk.Label(
            self.history_panel,
            text="SAN notation",
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.move_list_subtitle.pack(fill="x", pady=(0, 8))

        list_frame = tk.Frame(self.history_panel, bg=self.ui_theme.card_bg)
        list_frame.pack(fill="both", expand=True)
        self._theme_surfaces.append(list_frame)
        self.move_list = tk.Listbox(
            list_frame,
            height=24,
            activestyle="none",
            font=("Consolas", 11),
            bg=self.ui_theme.list_bg,
            fg=self.ui_theme.text,
            highlightthickness=0,
            borderwidth=0,
            selectbackground=self.ui_theme.accent,
            relief="flat",
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.move_list.yview)
        self.move_list.configure(yscrollcommand=scroll.set)
        self.move_list.pack(side=tk.LEFT, fill="both", expand=True)
        scroll.pack(side=tk.RIGHT, fill="y")

        hint_box = tk.Frame(self.history_panel, bg=self.ui_theme.card_bg, height=42)
        hint_box.pack(fill="x", pady=(10, 0))
        hint_box.pack_propagate(False)
        self._theme_surfaces.append(hint_box)
        self.hint_label = tk.Label(
            hint_box,
            textvariable=self.hint_var,
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
            anchor="nw",
            justify="left",
            wraplength=250,
        )
        self.hint_label.pack(fill="both", expand=True)

    def _make_card(self, parent: tk.Misc, *, width: int) -> tuple[tk.Frame, tk.Frame]:
        border = tk.Frame(parent, bg=self.ui_theme.card_border, width=width, padx=1, pady=1)
        card = tk.Frame(border, bg=self.ui_theme.card_bg, padx=16, pady=14)
        card.pack(fill="both", expand=True)
        self._card_borders.append(border)
        self._theme_surfaces.append(card)
        return border, card

    def _add_section(self, parent: tk.Misc, title: str) -> None:
        divider = tk.Frame(parent, bg=self.ui_theme.card_border, height=1)
        divider.pack(fill="x", pady=(12, 8))
        self._card_borders.append(divider)
        label = tk.Label(
            parent,
            text=title.upper(),
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI Semibold", 8),
            anchor="w",
        )
        label.pack(fill="x", pady=(0, 6))
        self._section_labels.append(label)
        self._theme_surfaces.append(label)

    def _add_kv_row(self, parent: tk.Misc, key: str, value_var: tk.StringVar) -> None:
        row = tk.Frame(parent, bg=self.ui_theme.card_bg)
        row.pack(fill="x", pady=2)
        self._theme_surfaces.append(row)
        key_label = tk.Label(
            row,
            text=key,
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
            width=7,
            anchor="w",
        )
        key_label.pack(side=tk.LEFT)
        value_label = tk.Label(
            row,
            textvariable=value_var,
            bg=self.ui_theme.card_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=210,
        )
        value_label.pack(side=tk.LEFT, fill="x", expand=True)
        self._key_labels.append(key_label)
        self._value_labels.append(value_label)

    def _apply_theme_styles(self) -> None:
        theme = self.ui_theme
        self.root.configure(bg=theme.app_bg)
        self.shell.configure(bg=theme.app_bg)
        self.canvas.configure(background=self.board_theme.canvas_bg)
        for border in self._card_borders:
            border.configure(bg=theme.card_border)
        for surface in self._theme_surfaces:
            try:
                surface.configure(bg=theme.card_bg)
            except tk.TclError:
                pass
        self.panel.configure(bg=theme.card_bg)
        self.history_panel.configure(bg=theme.card_bg)
        self.title_label.configure(bg=theme.card_bg, fg=theme.text)
        self.subtitle_label.configure(bg=theme.card_bg, fg=theme.muted)
        self.move_list_title.configure(bg=theme.card_bg, fg=theme.text)
        self.move_list_subtitle.configure(bg=theme.card_bg, fg=theme.muted)
        self.difficulty_desc.configure(bg=theme.card_bg, fg=theme.muted)
        self.hint_label.configure(bg=theme.card_bg, fg=theme.muted)
        self.ai_badge.configure(
            bg=theme.accent_soft if self._ai_busy else theme.card_bg,
            fg=theme.accent,
        )
        for label in self._section_labels:
            label.configure(bg=theme.card_bg, fg=theme.muted)
        for label in self._key_labels:
            label.configure(bg=theme.card_bg, fg=theme.muted)
        for label in self._value_labels:
            label.configure(bg=theme.card_bg, fg=theme.text)
        self.move_list.configure(
            bg=theme.list_bg,
            fg=theme.text,
            selectbackground=theme.accent,
        )

    def _on_theme_changed(self) -> None:
        self.board_theme = BOARD_THEMES[self.board_theme_var.get()]
        self.ui_theme = UI_THEMES[self.ui_theme_var.get()]
        self._apply_theme_styles()
        self._redraw()

    def _on_difficulty_changed(self) -> None:
        diff = difficulty_from_label(self.difficulty_var.get())
        self.controller.set_difficulty(diff.key)
        self.difficulty_desc.configure(text=diff.description)
        self._refresh_panel(message=f"Difficulty set to {diff.label}.")

    def _on_new_game(self) -> None:
        if self._animating:
            return
        self.controller.start_new_game()
        self.selected = None
        self.target_squares.clear()
        self.capture_targets.clear()
        self.last_from = None
        self.last_to = None
        self._flash_to = None
        self._ai_busy = False
        self._hover = None
        self._hidden_positions.clear()
        self._redraw()
        self._refresh_panel(message="New game started. White to move.")

    def _on_undo(self) -> None:
        if self._ai_busy or self._animating:
            return
        if not self.controller.can_undo():
            self._refresh_panel(message="Nothing to undo")
            return
        result = self.controller.undo()
        self.selected = None
        self.target_squares.clear()
        self.capture_targets.clear()
        history = self.controller.get_move_history()
        if history:
            last = history[-1].move
            self.last_from = last.from_position
            self.last_to = last.to_position
        else:
            self.last_from = None
            self.last_to = None
        self._flash_to = None
        self._redraw()
        self._refresh_panel(message=result.message)

    def _on_copy_pgn(self) -> None:
        pgn = self.controller.to_pgn()
        self.root.clipboard_clear()
        self.root.clipboard_append(pgn)
        self.root.update_idletasks()
        self._refresh_panel(message="PGN copied to clipboard.")

    def _on_save_pgn(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save PGN",
            defaultextension=".pgn",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            initialfile="chessmind.pgn",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self.controller.to_pgn())
        except OSError as exc:
            messagebox.showerror("Save PGN failed", str(exc), parent=self.root)
            return
        self._refresh_panel(message=f"PGN saved: {path}")

    def _busy(self) -> bool:
        return self._ai_busy or self._animating

    def _on_motion(self, event: tk.Event) -> None:
        if self._busy():
            return
        try:
            hover = self.geometry.pixels_to_position(event.x, event.y)
        except InvalidPositionError:
            if self._hover is not None:
                self._hover = None
                self._redraw()
            return
        if hover != self._hover:
            self._hover = hover
            self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        if self._hover is not None:
            self._hover = None
            self._redraw()

    def _on_click(self, event: tk.Event) -> None:
        if self._busy():
            return
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            return
        if state.side_to_move is not Color.WHITE:
            return
        try:
            clicked = self.geometry.pixels_to_position(event.x, event.y)
        except InvalidPositionError:
            return

        if self.selected is None:
            piece = state.board.get_piece(clicked)
            if piece is None or piece.color is not Color.WHITE:
                self._refresh_panel(message="Select a white piece.")
                return
            self._select_square(clicked)
            return

        if clicked == self.selected:
            self.selected = None
            self.target_squares.clear()
            self.capture_targets.clear()
            self._redraw()
            self._refresh_panel(message="Selection cleared.")
            return

        piece = state.board.get_piece(clicked)
        if piece is not None and piece.color is Color.WHITE:
            self._select_square(clicked)
            return

        source = self.selected
        moving = state.board.get_piece(source)
        result = self.controller.make_player_move_from_notation(
            source.to_chess_notation(),
            clicked.to_chess_notation(),
        )
        self.selected = None
        self.target_squares.clear()
        self.capture_targets.clear()
        if not result.success or moving is None:
            self._redraw()
            self._refresh_panel(message=result.message)
            return

        self.last_from = source
        self.last_to = clicked
        self._animate_move(
            moving,
            source,
            clicked,
            on_done=lambda: self._after_player_move(source, clicked),
        )

    def _after_player_move(self, source: Position, clicked: Position) -> None:
        self._refresh_panel(
            message=f"You played {source.to_chess_notation()}{clicked.to_chess_notation()}."
        )
        self._maybe_finish_or_ai()

    def _select_square(self, clicked: Position) -> None:
        self.selected = clicked
        legal = [
            move
            for move in self.controller.get_legal_moves()
            if move.from_position == clicked
        ]
        self.target_squares = {move.to_position for move in legal}
        self.capture_targets = {
            move.to_position
            for move in legal
            if move.move_type in {MoveType.CAPTURE, MoveType.PROMOTION_CAPTURE}
        }
        self._redraw()
        self._refresh_panel(message=f"Selected {clicked.to_chess_notation()}.")

    def _set_interactive_controls(self, enabled: bool) -> None:
        state = "readonly" if enabled else "disabled"
        try:
            self.difficulty_box.configure(state=state)
        except tk.TclError:
            pass

    def _start_thinking_pulse(self) -> None:
        self._stop_thinking_pulse()
        self._think_dots = 0

        def pulse() -> None:
            if not self._ai_busy:
                return
            self._think_dots = (self._think_dots + 1) % 4
            dots = "." * self._think_dots
            self.hint_var.set(f"AI thinking{dots} (UI still responsive)")
            self.turn_var.set("Black")
            self.ai_badge.configure(
                text=" ● AI thinking",
                bg=self.ui_theme.accent_soft,
                fg=self.ui_theme.accent,
            )
            self._think_job = self.root.after(350, pulse)

        pulse()

    def _stop_thinking_pulse(self) -> None:
        self.ai_badge.configure(text="", bg=self.ui_theme.card_bg)
        if self._think_job is not None:
            try:
                self.root.after_cancel(self._think_job)
            except Exception:
                pass
            self._think_job = None

    def _maybe_finish_or_ai(self) -> None:
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            self._show_game_over()
            return
        if state.side_to_move is Color.BLACK:
            self._ai_busy = True
            self._set_interactive_controls(False)
            self._refresh_panel(message="AI thinking... (UI still responsive)")
            self._start_thinking_pulse()
            self.root.after(20, self._run_ai_move_async)

    def _run_ai_move_async(self) -> None:
        def worker() -> None:
            result = None
            search = None
            error: Exception | None = None
            try:
                result = self.controller.make_ai_move()
                search = self.controller.get_last_search_result()
            except Exception as exc:  # noqa: BLE001 - surfaced on UI thread
                error = exc
            self.root.after(
                0,
                lambda r=result, s=search, e=error: self._on_ai_search_finished(r, s, e),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _on_ai_search_finished(self, result, search, error: Exception | None) -> None:
        self._stop_thinking_pulse()
        if error is not None:
            self._ai_busy = False
            self._set_interactive_controls(True)
            self._redraw()
            self._refresh_panel(message=f"AI error: {error}")
            messagebox.showerror("AI error", str(error))
            return

        if result is not None and result.success and search and search.best_move is not None:
            move = search.best_move
            self.last_from = move.from_position
            self.last_to = move.to_position
            notation = (
                f"{move.from_position.to_chess_notation()}"
                f"{move.to_position.to_chess_notation()}"
            )
            self._animate_move(
                move.moving_piece,
                move.from_position,
                move.to_position,
                on_done=lambda: self._after_ai_move(result.message, notation, search),
            )
            return

        self._ai_busy = False
        self._set_interactive_controls(True)
        self._redraw()
        message = result.message if result is not None else "AI failed"
        self._refresh_panel(message=message)
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._show_game_over()

    def _after_ai_move(self, message: str, notation: str, search) -> None:
        self._ai_busy = False
        self._set_interactive_controls(True)
        self._refresh_panel(
            message=f"AI played {notation}.",
            ai_line=f"AI: {notation} (score {search.best_score})",
        )
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._show_game_over()

    def _animate_move(
        self,
        piece: Piece,
        source: Position,
        target: Position,
        on_done,
    ) -> None:
        self._animating = True
        self._hidden_positions = {source, target}
        self._flash_to = target
        self._redraw()

        x0, y0, x1, y1 = self.geometry.position_to_pixels(source)
        tx0, ty0, tx1, ty1 = self.geometry.position_to_pixels(target)
        start = ((x0 + x1) / 2, (y0 + y1) / 2)
        end = ((tx0 + tx1) / 2, (ty0 + ty1) / 2)

        try:
            image = self.piece_images.get(piece)
            floating = self.canvas.create_image(start[0], start[1], image=image)
            self._floating["image_ref"] = image
        except Exception:
            floating = self.canvas.create_text(
                start[0],
                start[1],
                text=piece_glyph(piece),
                font=("Segoe UI Symbol", 40),
            )

        # Destination pulse ring
        pulse = self.canvas.create_oval(
            tx0 + 6,
            ty0 + 6,
            tx1 - 6,
            ty1 - 6,
            outline="#ffffff",
            width=3,
        )

        step = {"i": 0}

        def tick() -> None:
            i = step["i"]
            if i >= _ANIM_STEPS:
                self.canvas.delete(floating)
                self.canvas.delete(pulse)
                self._floating.clear()
                self._hidden_positions.clear()
                self._animating = False
                self._redraw()
                on_done()
                return
            t = (i + 1) / _ANIM_STEPS
            # Ease out cubic
            te = 1 - (1 - t) ** 3
            x = start[0] + (end[0] - start[0]) * te
            y = start[1] + (end[1] - start[1]) * te
            self.canvas.coords(floating, x, y)
            # Shrink pulse slightly
            pad = 6 + int(4 * t)
            self.canvas.coords(pulse, tx0 + pad, ty0 + pad, tx1 - pad, ty1 - pad)
            step["i"] = i + 1
            self.root.after(_ANIM_INTERVAL_MS, tick)

        tick()

    def _show_game_over(self) -> None:
        pretty = format_status(self.controller.get_state().status)
        self._refresh_panel(message=f"Game over: {pretty}")
        messagebox.showinfo("Game over", pretty)

    def _checked_king_square(self) -> Position | None:
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

    def _refresh_panel(self, message: str | None = None, ai_line: str | None = None) -> None:
        state = self.controller.get_state()
        diff = self.controller.get_difficulty()
        self.mode_var.set(diff.label)
        turn = "White" if state.side_to_move is Color.WHITE else "Black"
        self.turn_var.set(turn)
        self.status_var.set(format_status(state.status))

        history = self.controller.get_move_history()
        if history:
            self.last_move_var.set(history[-1].notation)
        else:
            self.last_move_var.set("—")

        search = self.controller.get_last_search_result()
        if ai_line is not None:
            # Strip a leading "AI: " if callers still pass the old format.
            self.ai_info_var.set(ai_line.removeprefix("AI: ").strip())
        else:
            ai_entries = [entry for entry in history if not entry.by_player]
            if search is not None and ai_entries:
                self.ai_info_var.set(
                    f"{ai_entries[-1].notation}  ·  {search.best_score}"
                )
            else:
                self.ai_info_var.set("waiting")

        if self._ai_busy:
            self.ai_badge.configure(
                text=" ● AI thinking",
                bg=self.ui_theme.accent_soft,
                fg=self.ui_theme.accent,
            )
        elif not self.ai_badge.cget("text"):
            self.ai_badge.configure(bg=self.ui_theme.card_bg)

        if search is not None:
            self.stats_var.set(
                f"{search.statistics.nodes_visited} nodes · "
                f"{search.statistics.execution_time_ms:.0f} ms"
                + (
                    f" · d{search.statistics.max_depth_reached}"
                    if search.statistics.max_depth_reached
                    else ""
                )
            )
        else:
            self.stats_var.set("—")

        self.captured_white_var.set(
            "You  " + self._format_captured(self.controller.get_captured_pieces(Color.WHITE))
        )
        self.captured_black_var.set(
            "AI   " + self._format_captured(self.controller.get_captured_pieces(Color.BLACK))
        )

        self.move_list.delete(0, tk.END)
        for index in range(0, len(history), 2):
            white = history[index].notation
            black = history[index + 1].notation if index + 1 < len(history) else ""
            line = f"{index // 2 + 1:>2}. {white:<7} {black}"
            self.move_list.insert(tk.END, line)
            if (index // 2) % 2 == 1:
                self.move_list.itemconfigure(tk.END, background=self.ui_theme.row_alt)
        if history:
            self.move_list.see(tk.END)

        self.undo_btn.configure(
            state=("normal" if self.controller.can_undo() and not self._busy() else "disabled")
        )

        if message is not None:
            self.hint_var.set(message)

    def _redraw(self) -> None:
        self.canvas.delete("all")
        state = self.controller.get_state()
        checked = self._checked_king_square()
        theme = self.board_theme
        margin = self.geometry.margin
        board = self.geometry.board_pixels

        # Outer frame + inner bevel around the 8x8 grid.
        outer = 12
        self.canvas.create_rectangle(
            margin - outer,
            margin - outer,
            margin + board + outer,
            margin + board + outer,
            fill=theme.frame,
            outline=theme.frame_border,
            width=2,
        )
        self.canvas.create_rectangle(
            margin - 3,
            margin - 3,
            margin + board + 3,
            margin + board + 3,
            fill="",
            outline=theme.frame_border,
            width=1,
        )

        for row in range(8):
            for column in range(8):
                position = Position(row=row, column=column)
                x0, y0, x1, y1 = self.geometry.position_to_pixels(position)
                base = theme.light if (row + column) % 2 == 0 else theme.dark
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=base, outline="")

                # Soft overlays keep the square identity while highlighting.
                if position in {self.last_from, self.last_to}:
                    self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=theme.last, outline="", stipple="gray50"
                    )
                if position == self.selected or (
                    self._flash_to is not None and position == self._flash_to
                ):
                    self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=theme.select, outline="", stipple="gray50"
                    )
                    self.canvas.create_rectangle(
                        x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline=theme.select, width=2
                    )
                if checked is not None and position == checked:
                    self.canvas.create_rectangle(
                        x0, y0, x1, y1, fill=theme.check, outline="", stipple="gray50"
                    )
                    self.canvas.create_rectangle(
                        x0 + 3, y0 + 3, x1 - 3, y1 - 3, outline=theme.check, width=3
                    )

                if self._hover == position and position != self.selected:
                    self.canvas.create_rectangle(
                        x0 + 2,
                        y0 + 2,
                        x1 - 2,
                        y1 - 2,
                        outline=theme.hover,
                        width=2,
                    )

                if column == 0:
                    self.canvas.create_text(
                        margin // 2,
                        (y0 + y1) // 2,
                        text=str(8 - row),
                        fill=theme.coord,
                        font=("Segoe UI Semibold", 12),
                    )
                if row == 7:
                    self.canvas.create_text(
                        (x0 + x1) // 2,
                        margin + board + margin // 2,
                        text=chr(ord("a") + column),
                        fill=theme.coord,
                        font=("Segoe UI Semibold", 12),
                    )

                if position in self.target_squares:
                    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                    if position in self.capture_targets:
                        inset = max(7, self.geometry.square_size // 10)
                        self.canvas.create_oval(
                            x0 + inset,
                            y0 + inset,
                            x1 - inset,
                            y1 - inset,
                            outline=theme.hint_capture,
                            width=3,
                        )
                    else:
                        r = max(7, self.geometry.square_size // 7)
                        self.canvas.create_oval(
                            cx - r,
                            cy - r,
                            cx + r,
                            cy + r,
                            fill=theme.hint,
                            outline="",
                        )

                if position in self._hidden_positions:
                    continue

                piece = state.board.get_piece(position)
                if piece is not None:
                    try:
                        image = self.piece_images.get(piece)
                        self.canvas.create_image(
                            (x0 + x1) // 2, (y0 + y1) // 2 + 1, image=image
                        )
                    except Exception:
                        self.canvas.create_text(
                            (x0 + x1) // 2,
                            (y0 + y1) // 2,
                            text=piece_glyph(piece),
                            font=("Segoe UI Symbol", 42),
                        )


def run_gui(depth: int | None = None, difficulty: str = DEFAULT_DIFFICULTY_KEY) -> None:
    root = tk.Tk()
    key = difficulty
    if depth is not None:
        # Backward-compatible CLI --depth maps roughly onto presets.
        mapping = {1: "beginner", 2: "medium", 3: "hard", 4: "expert", 5: "expert"}
        key = mapping.get(depth, DEFAULT_DIFFICULTY_KEY)
    ChessGuiApp(root, difficulty_key=key)
    root.mainloop()
