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
    app = ChessGuiApp(tk_root, depth=1)
    assert app.controller.get_state().ply_count == 0
    assert app.canvas.winfo_exists() == 1
