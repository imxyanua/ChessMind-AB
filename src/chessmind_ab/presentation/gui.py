"""Tkinter GUI with PNG pieces, themes, captured list, moves, and undo."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

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

# Fallback glyphs if a sprite fails to load.
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


def piece_glyph(piece: Piece) -> str:
    return _PIECE_GLYPHS[(piece.type, piece.color)]


def format_status(status: GameStatus) -> str:
    return status.name.replace("_", " ").title()


class ChessGuiApp:
    def __init__(self, root: tk.Tk, depth: int = 3) -> None:
        self.root = root
        self.root.title("ChessMind-AB")
        self.root.resizable(False, False)

        self.board_theme: BoardTheme = BOARD_THEMES["green"]
        self.ui_theme: UiTheme = UI_THEMES["dark"]

        self.geometry = BoardGeometry(square_size=80, margin=32)
        self.piece_images = PieceImageCache(self.geometry.square_size)
        self.controller = GameController(ai_depth=depth, player_color=Color.WHITE)
        self.controller.start_new_game()

        self.selected: Position | None = None
        self.target_squares: set[Position] = set()
        self.capture_targets: set[Position] = set()
        self.last_from: Position | None = None
        self.last_to: Position | None = None
        self._ai_busy = False
        self._hover: Position | None = None

        self._build_layout(depth)
        self._apply_theme_styles()
        self._redraw()
        self._refresh_panel()

    def _build_layout(self, depth: int) -> None:
        self.shell = tk.Frame(self.root, bg=self.ui_theme.app_bg, padx=12, pady=12)
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

        self.panel = tk.Frame(self.shell, bg=self.ui_theme.panel_bg, padx=16, pady=16)
        self.panel.grid(row=0, column=1, sticky="ns", padx=(14, 0))
        self.panel.configure(width=300)
        self.panel.grid_propagate(False)

        self.title_label = tk.Label(
            self.panel,
            text="ChessMind-AB",
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI Semibold", 14),
            anchor="w",
        )
        self.title_label.pack(fill="x")
        self.subtitle_label = tk.Label(
            self.panel,
            text="Player (White) vs AI (Black)",
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(0, 10))

        self.turn_var = tk.StringVar(value="Turn: White")
        self.status_var = tk.StringVar(value="Status: Ongoing")
        self.last_move_var = tk.StringVar(value="Last move: —")
        self.ai_info_var = tk.StringVar(value="AI: waiting")
        self.stats_var = tk.StringVar(value="Nodes: — | Time: —")
        self.hint_var = tk.StringVar(value="Click a white piece, then a marked square.")
        self.captured_white_var = tk.StringVar(value="You captured: —")
        self.captured_black_var = tk.StringVar(value="AI captured: —")

        self._info_labels: list[tk.Label] = []
        for var in (
            self.turn_var,
            self.status_var,
            self.last_move_var,
            self.ai_info_var,
            self.stats_var,
            self.captured_white_var,
            self.captured_black_var,
        ):
            label = tk.Label(
                self.panel,
                textvariable=var,
                bg=self.ui_theme.panel_bg,
                fg=self.ui_theme.text,
                font=("Segoe UI", 10),
                anchor="w",
                justify="left",
            )
            label.pack(fill="x", pady=2)
            self._info_labels.append(label)

        tk.Frame(self.panel, bg=self.ui_theme.muted, height=1).pack(fill="x", pady=10)

        theme_row = tk.Frame(self.panel, bg=self.ui_theme.panel_bg)
        theme_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            theme_row,
            text="Board",
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT)
        self.board_theme_var = tk.StringVar(value="green")
        ttk.Combobox(
            theme_row,
            textvariable=self.board_theme_var,
            values=list(BOARD_THEMES.keys()),
            width=8,
            state="readonly",
        ).pack(side=tk.RIGHT)
        self.board_theme_var.trace_add("write", lambda *_: self._on_theme_changed())

        ui_row = tk.Frame(self.panel, bg=self.ui_theme.panel_bg)
        ui_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            ui_row,
            text="UI",
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT)
        self.ui_theme_var = tk.StringVar(value="dark")
        ttk.Combobox(
            ui_row,
            textvariable=self.ui_theme_var,
            values=list(UI_THEMES.keys()),
            width=8,
            state="readonly",
        ).pack(side=tk.RIGHT)
        self.ui_theme_var.trace_add("write", lambda *_: self._on_theme_changed())

        depth_row = tk.Frame(self.panel, bg=self.ui_theme.panel_bg)
        depth_row.pack(fill="x", pady=(0, 8))
        tk.Label(
            depth_row,
            text="AI depth",
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT)
        self.depth_var = tk.IntVar(value=depth)
        ttk.Spinbox(
            depth_row,
            from_=1,
            to=5,
            width=4,
            textvariable=self.depth_var,
            command=self._on_depth_changed,
        ).pack(side=tk.RIGHT)

        btn_row = tk.Frame(self.panel, bg=self.ui_theme.panel_bg)
        btn_row.pack(fill="x", pady=(4, 8))
        ttk.Button(btn_row, text="New Game", command=self._on_new_game).pack(
            side=tk.LEFT, expand=True, fill="x", padx=(0, 4)
        )
        ttk.Button(btn_row, text="Undo", command=self._on_undo).pack(
            side=tk.LEFT, expand=True, fill="x", padx=(4, 0)
        )

        tk.Label(
            self.panel,
            text="Move list",
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.text,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(fill="x", pady=(6, 2))

        list_frame = tk.Frame(self.panel, bg=self.ui_theme.panel_bg)
        list_frame.pack(fill="both", expand=True)
        self.move_list = tk.Listbox(
            list_frame,
            height=12,
            activestyle="dotbox",
            font=("Consolas", 10),
            bg="#1f2330" if self.ui_theme.name == "dark" else "#f7f8fb",
            fg=self.ui_theme.text,
            highlightthickness=0,
            borderwidth=0,
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.move_list.yview)
        self.move_list.configure(yscrollcommand=scroll.set)
        self.move_list.pack(side=tk.LEFT, fill="both", expand=True)
        scroll.pack(side=tk.RIGHT, fill="y")

        self.hint_label = tk.Label(
            self.panel,
            textvariable=self.hint_var,
            bg=self.ui_theme.panel_bg,
            fg=self.ui_theme.muted,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=260,
        )
        self.hint_label.pack(fill="x", pady=(10, 0))

    def _apply_theme_styles(self) -> None:
        self.root.configure(bg=self.ui_theme.app_bg)
        self.shell.configure(bg=self.ui_theme.app_bg)
        self.panel.configure(bg=self.ui_theme.panel_bg)
        self.canvas.configure(background=self.board_theme.canvas_bg)
        for widget in (self.title_label, self.subtitle_label, self.hint_label, *self._info_labels):
            widget.configure(bg=self.ui_theme.panel_bg)
        self.title_label.configure(fg=self.ui_theme.text)
        self.subtitle_label.configure(fg=self.ui_theme.muted)
        self.hint_label.configure(fg=self.ui_theme.muted)
        for label in self._info_labels:
            label.configure(fg=self.ui_theme.text)
        list_bg = "#1f2330" if self.ui_theme.name == "dark" else "#f7f8fb"
        self.move_list.configure(bg=list_bg, fg=self.ui_theme.text)

    def _on_theme_changed(self) -> None:
        self.board_theme = BOARD_THEMES[self.board_theme_var.get()]
        self.ui_theme = UI_THEMES[self.ui_theme_var.get()]
        self._apply_theme_styles()
        self._redraw()

    def _on_depth_changed(self) -> None:
        self.controller.set_ai_depth(int(self.depth_var.get()))

    def _on_new_game(self) -> None:
        self.controller.start_new_game()
        self.controller.set_ai_depth(int(self.depth_var.get()))
        self.selected = None
        self.target_squares.clear()
        self.capture_targets.clear()
        self.last_from = None
        self.last_to = None
        self._ai_busy = False
        self._hover = None
        self._redraw()
        self._refresh_panel(message="New game started. White to move.")

    def _on_undo(self) -> None:
        if self._ai_busy:
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
        self._redraw()
        self._refresh_panel(message=result.message)

    def _on_motion(self, event: tk.Event) -> None:
        if self._ai_busy:
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
        if self._ai_busy:
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
        result = self.controller.make_player_move_from_notation(
            source.to_chess_notation(),
            clicked.to_chess_notation(),
        )
        self.selected = None
        self.target_squares.clear()
        self.capture_targets.clear()
        if not result.success:
            self._redraw()
            self._refresh_panel(message=result.message)
            return

        self.last_from = source
        self.last_to = clicked
        self._redraw()
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

    def _maybe_finish_or_ai(self) -> None:
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            self._show_game_over()
            return
        if state.side_to_move is Color.BLACK:
            self._ai_busy = True
            self._refresh_panel(message="AI thinking...")
            self.root.after(40, self._run_ai_move)

    def _run_ai_move(self) -> None:
        try:
            result = self.controller.make_ai_move()
        except Exception as exc:  # noqa: BLE001 - keep UI responsive on search bugs
            self._ai_busy = False
            self._redraw()
            self._refresh_panel(message=f"AI error: {exc}")
            messagebox.showerror("AI error", str(exc))
            return

        self._ai_busy = False
        search = self.controller.get_last_search_result()
        if result.success and search and search.best_move is not None:
            self.last_from = search.best_move.from_position
            self.last_to = search.best_move.to_position
            notation = (
                f"{search.best_move.from_position.to_chess_notation()}"
                f"{search.best_move.to_position.to_chess_notation()}"
            )
            self._redraw()
            self._refresh_panel(
                message=f"AI played {notation}.",
                ai_line=f"AI: {notation} (score {search.best_score})",
            )
        else:
            self._redraw()
            self._refresh_panel(message=result.message)
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._show_game_over()

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
        turn = "White" if state.side_to_move is Color.WHITE else "Black"
        if self._ai_busy:
            turn = "Black (AI thinking)"
        self.turn_var.set(f"Turn: {turn}")
        self.status_var.set(f"Status: {format_status(state.status)}")

        if self.last_from is not None and self.last_to is not None:
            self.last_move_var.set(
                "Last move: "
                f"{self.last_from.to_chess_notation()}{self.last_to.to_chess_notation()}"
            )
        else:
            self.last_move_var.set("Last move: —")

        search = self.controller.get_last_search_result()
        if ai_line is not None:
            self.ai_info_var.set(ai_line)
        elif search and search.best_move is not None:
            notation = (
                f"{search.best_move.from_position.to_chess_notation()}"
                f"{search.best_move.to_position.to_chess_notation()}"
            )
            self.ai_info_var.set(f"AI: {notation} (score {search.best_score})")
        else:
            self.ai_info_var.set("AI: waiting")

        if search is not None:
            self.stats_var.set(
                f"Nodes: {search.statistics.nodes_visited} | "
                f"Time: {search.statistics.execution_time_ms:.0f} ms"
            )
        else:
            self.stats_var.set("Nodes: — | Time: —")

        self.captured_white_var.set(
            "You captured: "
            + self._format_captured(self.controller.get_captured_pieces(Color.WHITE))
        )
        self.captured_black_var.set(
            "AI captured: "
            + self._format_captured(self.controller.get_captured_pieces(Color.BLACK))
        )

        self.move_list.delete(0, tk.END)
        history = self.controller.get_move_history()
        for index in range(0, len(history), 2):
            white = history[index].notation
            black = history[index + 1].notation if index + 1 < len(history) else ""
            self.move_list.insert(tk.END, f"{index // 2 + 1}. {white}  {black}")
        if history:
            self.move_list.see(tk.END)

        if message is not None:
            self.hint_var.set(message)

    def _redraw(self) -> None:
        self.canvas.delete("all")
        state = self.controller.get_state()
        checked = self._checked_king_square()
        theme = self.board_theme

        pad = 6
        self.canvas.create_rectangle(
            self.geometry.margin - pad,
            self.geometry.margin - pad,
            self.geometry.margin + self.geometry.board_pixels + pad,
            self.geometry.margin + self.geometry.board_pixels + pad,
            fill="#0f1116",
            outline="#3a4050",
            width=2,
        )

        for row in range(8):
            for column in range(8):
                position = Position(row=row, column=column)
                x0, y0, x1, y1 = self.geometry.position_to_pixels(position)
                color = theme.light if (row + column) % 2 == 0 else theme.dark
                if position == self.selected:
                    color = theme.select
                elif position in {self.last_from, self.last_to}:
                    color = theme.last
                if checked is not None and position == checked:
                    color = theme.check
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

                if self._hover == position and position != self.selected:
                    self.canvas.create_rectangle(
                        x0 + 2, y0 + 2, x1 - 2, y1 - 2, outline="#ffffff", width=2
                    )

                if column == 0:
                    self.canvas.create_text(
                        self.geometry.margin // 2,
                        (y0 + y1) // 2,
                        text=str(8 - row),
                        fill=theme.coord,
                        font=("Segoe UI Semibold", 11),
                    )
                if row == 7:
                    self.canvas.create_text(
                        (x0 + x1) // 2,
                        self.geometry.margin
                        + self.geometry.board_pixels
                        + self.geometry.margin // 2,
                        text=chr(ord("a") + column),
                        fill=theme.coord,
                        font=("Segoe UI Semibold", 11),
                    )

                if position in self.target_squares:
                    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                    if position in self.capture_targets:
                        self.canvas.create_oval(
                            x0 + 8, y0 + 8, x1 - 8, y1 - 8, outline="#111111", width=4
                        )
                    else:
                        r = max(8, self.geometry.square_size // 6)
                        self.canvas.create_oval(
                            cx - r, cy - r, cx + r, cy + r, fill="#1f2421", outline=""
                        )

                piece = state.board.get_piece(position)
                if piece is not None:
                    try:
                        image = self.piece_images.get(piece)
                        self.canvas.create_image(
                            (x0 + x1) // 2, (y0 + y1) // 2, image=image
                        )
                    except Exception:
                        self.canvas.create_text(
                            (x0 + x1) // 2,
                            (y0 + y1) // 2,
                            text=piece_glyph(piece),
                            font=("Segoe UI Symbol", 40),
                        )


def run_gui(depth: int = 3) -> None:
    root = tk.Tk()
    ChessGuiApp(root, depth=depth)
    root.mainloop()
