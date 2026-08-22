"""Tkinter graphical UI for Player vs AI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
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

_LIGHT = "#f0d9b5"
_DARK = "#b58863"
_SELECT = "#f6f669"
_TARGET = "#aad751"
_LAST = "#cdd26a"


def piece_glyph(piece: Piece) -> str:
    return _PIECE_GLYPHS[(piece.type, piece.color)]


class ChessGuiApp:
    def __init__(self, root: tk.Tk, depth: int = 2) -> None:
        self.root = root
        self.root.title("ChessMind-AB")
        self.root.resizable(False, False)

        self.geometry = BoardGeometry(square_size=72, margin=28)
        self.controller = GameController(ai_depth=depth, player_color=Color.WHITE)
        self.controller.start_new_game()

        self.selected: Position | None = None
        self.target_squares: set[Position] = set()
        self.last_from: Position | None = None
        self.last_to: Position | None = None
        self._ai_busy = False

        self._build_layout(depth)
        self._redraw()

    def _build_layout(self, depth: int) -> None:
        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Button(toolbar, text="New Game", command=self._on_new_game).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Label(toolbar, text="AI depth").pack(side=tk.LEFT)
        self.depth_var = tk.IntVar(value=depth)
        ttk.Spinbox(
            toolbar,
            from_=1,
            to=4,
            width=4,
            textvariable=self.depth_var,
            command=self._on_depth_changed,
        ).pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="White to move")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        size = self.geometry.board_pixels + self.geometry.margin * 2
        self.canvas = tk.Canvas(
            self.root,
            width=size,
            height=size,
            background="#333333",
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=0, padx=8, pady=(0, 8))
        self.canvas.bind("<Button-1>", self._on_click)

        ttk.Label(
            self.root,
            text="Click a white piece, then a highlighted square. AI replies automatically.",
            padding=(8, 0, 8, 8),
        ).grid(row=2, column=0, sticky="w")

    def _on_depth_changed(self) -> None:
        self.controller.set_ai_depth(int(self.depth_var.get()))

    def _on_new_game(self) -> None:
        self.controller.start_new_game()
        self.controller.set_ai_depth(int(self.depth_var.get()))
        self.selected = None
        self.target_squares.clear()
        self.last_from = None
        self.last_to = None
        self._ai_busy = False
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
                self.status_var.set("Select a white piece")
                return
            self.selected = clicked
            self.target_squares = {
                move.to_position
                for move in self.controller.get_legal_moves()
                if move.from_position == clicked
            }
            self._redraw()
            self.status_var.set(f"Selected {clicked.to_chess_notation()}")
            return

        if clicked == self.selected:
            self.selected = None
            self.target_squares.clear()
            self._redraw()
            self.status_var.set("Selection cleared")
            return

        source = self.selected
        result = self.controller.make_player_move_from_notation(
            source.to_chess_notation(),
            clicked.to_chess_notation(),
        )
        self.selected = None
        self.target_squares.clear()
        if not result.success:
            self.status_var.set(result.message)
            self._redraw()
            return

        self.last_from = source
        self.last_to = clicked
        self._redraw()
        self.status_var.set(f"Played {source.to_chess_notation()}{clicked.to_chess_notation()}")
        self._maybe_finish_or_ai()

    def _maybe_finish_or_ai(self) -> None:
        state = self.controller.get_state()
        if state.status is not GameStatus.ONGOING:
            self._show_game_over()
            return
        if state.side_to_move is Color.BLACK:
            self._ai_busy = True
            self.status_var.set("AI thinking...")
            self.root.after(50, self._run_ai_move)

    def _run_ai_move(self) -> None:
        result = self.controller.make_ai_move()
        self._ai_busy = False
        search = self.controller.get_last_search_result()
        if result.success and search and search.best_move is not None:
            self.last_from = search.best_move.from_position
            self.last_to = search.best_move.to_position
            self.status_var.set(
                "AI "
                f"{search.best_move.from_position.to_chess_notation()}"
                f"{search.best_move.to_position.to_chess_notation()}"
                f" (score {search.best_score})"
            )
        else:
            self.status_var.set(result.message)
        self._redraw()
        if self.controller.get_state().status is not GameStatus.ONGOING:
            self._show_game_over()

    def _show_game_over(self) -> None:
        status = self.controller.get_state().status
        self.status_var.set(f"Game over: {status.name}")
        messagebox.showinfo("Game over", status.name.replace("_", " "))

    def _square_color(self, position: Position) -> str:
        if self.selected == position:
            return _SELECT
        if position in self.target_squares:
            return _TARGET
        if position in {self.last_from, self.last_to}:
            return _LAST
        return _LIGHT if (position.row + position.column) % 2 == 0 else _DARK

    def _redraw(self) -> None:
        self.canvas.delete("all")
        state = self.controller.get_state()
        for row in range(8):
            for column in range(8):
                position = Position(row=row, column=column)
                x0, y0, x1, y1 = self.geometry.position_to_pixels(position)
                self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill=self._square_color(position), outline=""
                )
                if column == 0:
                    self.canvas.create_text(
                        self.geometry.margin // 2,
                        (y0 + y1) // 2,
                        text=str(8 - row),
                        fill="white",
                        font=("Segoe UI", 10, "bold"),
                    )
                if row == 7:
                    self.canvas.create_text(
                        (x0 + x1) // 2,
                        self.geometry.margin
                        + self.geometry.board_pixels
                        + self.geometry.margin // 2,
                        text=chr(ord("a") + column),
                        fill="white",
                        font=("Segoe UI", 10, "bold"),
                    )
                piece = state.board.get_piece(position)
                if piece is not None:
                    self.canvas.create_text(
                        (x0 + x1) // 2,
                        (y0 + y1) // 2,
                        text=piece_glyph(piece),
                        font=("Segoe UI Symbol", 36),
                    )

        if state.status is GameStatus.ONGOING and state.side_to_move is Color.WHITE:
            if self.selected is None and not self.status_var.get().startswith("AI"):
                self.status_var.set("White to move")


def run_gui(depth: int = 2) -> None:
    root = tk.Tk()
    ChessGuiApp(root, depth=depth)
    root.mainloop()
