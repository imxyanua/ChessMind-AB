"""Smoke tests for the PySide6 GUI (offscreen)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from chessmind_ab.domain.color import Color
from chessmind_ab.presentation.qt_gui import ChessMainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_qt_main_window_builds(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    assert window.controller.get_state().ply_count == 0
    assert window.turn_value.text() == "White"
    assert "Beginner" in window.diff_box.currentText()
    window._refresh(message="Ready")
    assert window.hint.text() == "Ready"
    window.close()


def test_qt_play_as_black_flips_board(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    window.side_box.setCurrentText("Black")
    assert window.controller.get_player_color() is Color.BLACK
    assert window.board.geometry_helper.flipped is True
    if window._worker is not None:
        window._worker.wait(8000)
        qapp.processEvents()
    window.close()


def test_qt_panels_match_board_height_and_actions_are_wide(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    board_h = window.board.height()
    assert window.info_card.height() == board_h
    assert window.hist_card.height() == board_h
    for btn in (window.new_btn, window.undo_btn, window.copy_btn, window.save_btn):
        assert btn.minimumWidth() >= 140
        assert btn.minimumHeight() >= 36
    window.close()
