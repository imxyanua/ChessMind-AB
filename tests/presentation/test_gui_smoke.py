"""Smoke test: GUI app can be constructed without entering mainloop."""

import tkinter as tk

import pytest

from chessmind_ab.application.difficulty import DIFFICULTIES
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.position import Position
from chessmind_ab.presentation.gui import ChessGuiApp


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk not available: {exc}")
    root.withdraw()
    yield root
    root.destroy()


def test_chess_gui_app_builds(tk_root) -> None:
    app = ChessGuiApp(tk_root, difficulty_key="beginner")
    assert app.controller.get_state().ply_count == 0
    assert app.canvas.winfo_exists() == 1
    assert app.turn_var.get() in {"White", "Black"}
    assert "Ongoing" in app.status_var.get()
    assert "Elo" in app.mode_var.get()
    app._refresh_panel(message="Ready")
    assert app.hint_var.get() == "Ready"
    assert app.board_theme_var.get() in {"green", "wood"}
    assert app.ui_theme_var.get() in {"dark", "light"}
    assert "Beginner" in app.difficulty_var.get()


def test_ai_async_helpers_exist(tk_root) -> None:
    app = ChessGuiApp(tk_root, difficulty_key="beginner")
    assert hasattr(app, "_run_ai_move_async")
    assert hasattr(app, "_on_ai_search_finished")
    app._ai_busy = True
    app._start_thinking_pulse()
    app._stop_thinking_pulse()
    app._ai_busy = False


def test_pgn_and_undo_controls_exist(tk_root) -> None:
    app = ChessGuiApp(tk_root, difficulty_key="beginner")
    assert hasattr(app, "_on_copy_pgn")
    assert hasattr(app, "_on_save_pgn")
    assert str(app.undo_btn.cget("state")) == "disabled"
    pgn = app.controller.to_pgn()
    assert '[Event "ChessMind-AB Game"]' in pgn
    app._on_copy_pgn()
    assert "clipboard" in app.hint_var.get().lower() or "PGN" in app.hint_var.get()


def test_board_polish_redraw_keeps_theme_fields(tk_root) -> None:
    app = ChessGuiApp(tk_root, difficulty_key="beginner")
    assert app.geometry.square_size == 88
    assert app.board_theme.frame_border
    app.last_from = Position.from_chess_notation("e2")
    app.last_to = Position.from_chess_notation("e4")
    app.selected = Position.from_chess_notation("g1")
    app._hover = Position.from_chess_notation("f3")
    app.target_squares = {Position.from_chess_notation("f3")}
    app.capture_targets = {Position.from_chess_notation("e5")}
    app._redraw()
    assert app.canvas.find_all()
    assert app.controller.get_state().side_to_move is Color.WHITE


def test_wider_three_column_layout(tk_root) -> None:
    app = ChessGuiApp(tk_root, difficulty_key="beginner")
    assert app.panel.winfo_exists() == 1
    assert app.history_panel.winfo_exists() == 1
    assert int(app.panel_border.cget("width")) >= 280
    assert int(app.history_border.cget("width")) >= 260
    assert int(app.move_list.cget("height")) >= 20
    app.ui_theme_var.set("light")
    app._on_theme_changed()
    assert app.history_panel.cget("bg") == app.ui_theme.card_bg


def test_difficulty_description_box_stays_fixed(tk_root) -> None:
    app = ChessGuiApp(tk_root, difficulty_key="beginner")
    desc_parent = app.difficulty_desc.master
    assert int(desc_parent.cget("height")) >= 36
    before = int(desc_parent.cget("height"))
    for diff in DIFFICULTIES.values():
        app.difficulty_var.set(diff.label)
        app.root.update_idletasks()
        assert int(desc_parent.cget("height")) == before
