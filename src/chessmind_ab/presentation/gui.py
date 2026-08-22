"""Tkinter graphical UI for Player vs AI with polished board and info panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import InvalidPositionError, Position
from chessmind_ab.presentation.board_geometry import BoardGeometry

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

# Visual theme
_APP_BG = "#1b1d24"
_PANEL_BG = "#252833"
_CANVAS_BG = "#14161c"
_LIGHT = "#ebecd0"
_DARK = "#739552"
_SELECT = "#f6f669"
_LAST = "#cdd26a"
_CHECK = "#e35d6a"
_COORD = "#c8cdd8"
_DOT = "#1f2421"
_CAPTURE_RING = "#111111"


def piece_glyph(piece: Piece) -> str:
    return _PIECE_GLYPHS[(piece.type, piece.color)]


def format_status(status: GameStatus) -> str:
    return status.name.replace("_", " ").title()


class ChessGuiApp:
    def __init__(self, root: tk.Tk, depth: int = 3) -> None:
        self.root = root
        self.root.title("ChessMind-AB")
        self.root.resizable(False, False)
        self.root.configure(bg=_APP_BG)

        self.geometry = BoardGeometry(square_size=80, margin=32)
        self.controller = GameController(ai_depth=depth, player_color=Color.WHITE)
        self.controller.start_new_game()

        self.selected: Position | None = None
        self.target_squares: set[Position] = set()
        self.capture_targets: set[Position] = set()
        self.last_from: Position | None = None
        self.last_to: Position | None = None
        self._ai_busy = False
        self._hover: Position | None = None

        self._configure_style()
        self._build_layout(depth)
        self._redraw()
        self._refresh_panel()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("App.TFrame", background=_APP_BG)
        style.configure("Panel.TFrame", background=_PANEL_BG)
        style.configure(
            "Panel.TLabel",
            background=_PANEL_BG,
            foreground="#e8ecf4",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=_PANEL_BG,
            foreground="#ffffff",
            font=("Segoe UI Semibold", 14),
        )
        style.configure(
            "Muted.TLabel",
            background=_PANEL_BG,
            foreground="#9aa3b5",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(12, 8),
        )

    def _build_layout(self, depth: int) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=12)
        shell.grid(row=0, column=0, sticky="nsew")

        board_wrap = ttk.Frame(shell, style="App.TFrame")
        board_wrap.grid(row=0, column=0, sticky="n")

        size = self.geometry.board_pixels + self.geometry.margin * 2
        self.canvas = tk.Canvas(
            board_wrap,
            width=size,
            height=size,
            background=_CANVAS_BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

        panel = ttk.Frame(shell, style="Panel.TFrame", padding=16)
        panel.grid(row=0, column=1, sticky="ns", padx=(14, 0))
        panel.configure(width=260)
        panel.grid_propagate(False)

        ttk.Label(panel, text="ChessMind-AB", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            panel,
            text="Player (White) vs AI (Black)",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 14))

        self.turn_var = tk.StringVar(value="Turn: White")
        self.status_var = tk.StringVar(value="Status: Ongoing")
        self.last_move_var = tk.StringVar(value="Last move: —")
        self.ai_info_var = tk.StringVar(value="AI: waiting")
        self.stats_var = tk.StringVar(value="Nodes: — | Time: —")
        self.hint_var = tk.StringVar(
            value="Click a white piece, then a highlighted square."
        )

        for var in (
            self.turn_var,
            self.status_var,
            self.last_move_var,
            self.ai_info_var,
            self.stats_var,
        ):
            ttk.Label(panel, textvariable=var, style="Panel.TLabel").pack(
                anchor="w", pady=3
            )

        ttk.Separator(panel).pack(fill="x", pady=12)

        depth_row = ttk.Frame(panel, style="Panel.TFrame")
        depth_row.pack(fill="x", pady=(0, 10))
        ttk.Label(depth_row, text="AI depth", style="Panel.TLabel").pack(side=tk.LEFT)
        self.depth_var = tk.IntVar(value=depth)
        ttk.Spinbox(
            depth_row,
            from_=1,
            to=5,
            width=4,
            textvariable=self.depth_var,
            command=self._on_depth_changed,
        ).pack(side=tk.RIGHT)

        ttk.Button(
            panel,
            text="New Game",
            style="Accent.TButton",
            command=self._on_new_game,
        ).pack(fill="x", pady=(4, 12))

        ttk.Label(panel, textvariable=self.hint_var, style="Muted.TLabel", wraplength=220).pack(
            anchor="w"
        )

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

        # Clicking another own piece reselects.
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
        notation = f"{source.to_chess_notation()}{clicked.to_chess_notation()}"
        self._redraw()
        self._refresh_panel(message=f"You played {notation}.")
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
        result = self.controller.make_ai_move()
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
        status = self.controller.get_state().status
        pretty = format_status(status)
        self._refresh_panel(message=f"Game over: {pretty}")
        messagebox.showinfo("Game over", pretty)

    def _checked_king_square(self) -> Position | None:
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            return None
        if AttackDetector.is_king_in_check(state, state.side_to_move):
            return state.board.find_king(state.side_to_move)
        return None

    def _base_square_color(self, position: Position) -> str:
        return _LIGHT if (position.row + position.column) % 2 == 0 else _DARK

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

        if message is not None:
            self.hint_var.set(message)

    def _redraw(self) -> None:
        self.canvas.delete("all")
        state = self.controller.get_state()
        checked = self._checked_king_square()

        # Soft outer frame
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
                color = self._base_square_color(position)
                if position == self.selected:
                    color = _SELECT
                elif position in {self.last_from, self.last_to}:
                    color = _LAST
                if checked is not None and position == checked:
                    color = _CHECK
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

                if self._hover == position and position != self.selected:
                    self.canvas.create_rectangle(
                        x0 + 2,
                        y0 + 2,
                        x1 - 2,
                        y1 - 2,
                        outline="#ffffff",
                        width=2,
                    )

                if column == 0:
                    self.canvas.create_text(
                        self.geometry.margin // 2,
                        (y0 + y1) // 2,
                        text=str(8 - row),
                        fill=_COORD,
                        font=("Segoe UI Semibold", 11),
                    )
                if row == 7:
                    self.canvas.create_text(
                        (x0 + x1) // 2,
                        self.geometry.margin
                        + self.geometry.board_pixels
                        + self.geometry.margin // 2,
                        text=chr(ord("a") + column),
                        fill=_COORD,
                        font=("Segoe UI Semibold", 11),
                    )

                # Legal move markers
                if position in self.target_squares:
                    cx = (x0 + x1) // 2
                    cy = (y0 + y1) // 2
                    if position in self.capture_targets:
                        self.canvas.create_oval(
                            x0 + 8,
                            y0 + 8,
                            x1 - 8,
                            y1 - 8,
                            outline=_CAPTURE_RING,
                            width=4,
                        )
                    else:
                        r = max(8, self.geometry.square_size // 6)
                        self.canvas.create_oval(
                            cx - r,
                            cy - r,
                            cx + r,
                            cy + r,
                            fill=_DOT,
                            outline="",
                        )

                piece = state.board.get_piece(position)
                if piece is not None:
                    cx = (x0 + x1) // 2
                    cy = (y0 + y1) // 2
                    glyph = piece_glyph(piece)
                    font = ("Segoe UI Symbol", 42)
                    # Outline for contrast on both light and dark squares.
                    for dx, dy in (
                        (-1, 0),
                        (1, 0),
                        (0, -1),
                        (0, 1),
                        (-1, -1),
                        (1, 1),
                        (-1, 1),
                        (1, -1),
                    ):
                        self.canvas.create_text(
                            cx + dx,
                            cy + dy,
                            text=glyph,
                            fill="#000000",
                            font=font,
                        )
                    fill = "#f8f8f8" if piece.color is Color.WHITE else "#1a1a1a"
                    self.canvas.create_text(cx, cy, text=glyph, fill=fill, font=font)


def run_gui(depth: int = 3) -> None:
    root = tk.Tk()
    ChessGuiApp(root, depth=depth)
    root.mainloop()
