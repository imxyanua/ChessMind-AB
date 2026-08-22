"""Smoke test: GUI app can be constructed without entering mainloop."""

import tkinter as tk

import pytest

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
    assert app.turn_var.get().startswith("Turn:")
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
