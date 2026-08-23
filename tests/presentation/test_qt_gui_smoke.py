"""Smoke tests for the PySide6 GUI (offscreen)."""

import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.presentation.qt_board import ChessBoardWidget
from chessmind_ab.presentation.qt_gui import ChessMainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _wait_until(qapp, predicate, timeout_s: float = 2.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


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
        _wait_until(
            qapp,
            lambda: not window._animating and not window.board.is_animating,
            timeout_s=3.0,
        )
    window.close()


def test_qt_panels_match_board_height_and_actions_are_wide(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    board_h = window.board.height()
    assert window.info_card.height() == board_h
    assert window.hist_card.height() == board_h
    assert window.info_card.width() >= 352
    assert window.new_btn.objectName() == "primary"
    for btn in (window.new_btn, window.undo_btn, window.copy_btn, window.save_btn):
        assert btn.minimumWidth() >= 150
        assert btn.minimumHeight() >= 40
        assert btn.toolTip()
    window.close()


def test_qt_board_animate_move_completes(qapp) -> None:
    board = ChessBoardWidget()
    done = {"ok": False}

    def _finish() -> None:
        done["ok"] = True

    piece = Piece(type=PieceType.PAWN, color=Color.WHITE)
    board.animate_move(
        piece,
        Position(row=6, column=4),
        Position(row=4, column=4),
        on_finished=_finish,
        duration_ms=50,
    )
    assert board.is_animating
    assert board._float_piece is piece
    assert _wait_until(qapp, lambda: done["ok"], timeout_s=2.0)
    assert not board.is_animating
    assert board._float_piece is None
    assert board.hidden == set()
    board.close()


def test_qt_player_move_uses_animation(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    e2 = Position.from_chess_notation("e2")
    e4 = Position.from_chess_notation("e4")
    window._on_square_clicked(e2)
    window._on_square_clicked(e4)
    assert window._animating or window.board.is_animating
    assert window.last_from == e2
    assert window.last_to == e4
    assert _wait_until(
        qapp,
        lambda: not window._animating and not window.board.is_animating,
        timeout_s=2.0,
    )
    assert window.controller.get_state().ply_count >= 1
    if window._worker is not None:
        window._worker.wait(8000)
        qapp.processEvents()
        _wait_until(
            qapp,
            lambda: not window._animating and not window.board.is_animating,
            timeout_s=3.0,
        )
    window.close()
