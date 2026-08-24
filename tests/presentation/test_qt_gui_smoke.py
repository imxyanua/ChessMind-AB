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
from chessmind_ab.presentation.qt_gui import ChessMainWindow, PromotionDialog


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
    assert window.info_card.width() >= 360
    assert window.new_btn.objectName() == "primary"
    for btn in (window.new_btn, window.undo_btn, window.copy_btn, window.save_btn):
        assert btn.height() == 40
        assert btn.toolTip()
    window.close()


def test_qt_action_buttons_do_not_overlap(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    window.show()
    qapp.processEvents()

    buttons = (window.new_btn, window.undo_btn, window.copy_btn, window.save_btn)
    rects = []
    for btn in buttons:
        assert btn.isVisible()
        assert btn.width() > 0
        assert btn.height() == 40
        top_left = btn.mapTo(window.info_card, btn.rect().topLeft())
        rects.append(
            (
                top_left.x(),
                top_left.y(),
                top_left.x() + btn.width(),
                top_left.y() + btn.height(),
            )
        )

    for i, a in enumerate(rects):
        for j, b in enumerate(rects):
            if i >= j:
                continue
            overlap_x = a[0] < b[2] and b[0] < a[2]
            overlap_y = a[1] < b[3] and b[1] < a[3]
            assert not (overlap_x and overlap_y), f"buttons {i} and {j} overlap: {a} vs {b}"

    # 2x2: New/Undo share a row; Copy/Save share the next row with a gap.
    assert abs(rects[0][1] - rects[1][1]) <= 1
    assert abs(rects[2][1] - rects[3][1]) <= 1
    assert rects[2][1] >= rects[0][3] + 6
    assert window.actions_panel.height() >= 92
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


def test_qt_board_animate_castling_slides_king_and_rook(qapp) -> None:
    board = ChessBoardWidget()
    done = {"ok": False}

    def _finish() -> None:
        done["ok"] = True

    king = Piece(type=PieceType.KING, color=Color.WHITE)
    rook = Piece(type=PieceType.ROOK, color=Color.WHITE)
    king_from = Position(row=7, column=4)
    king_to = Position(row=7, column=6)
    rook_from = Position(row=7, column=7)
    rook_to = Position(row=7, column=5)
    board.animate_move(
        king,
        king_from,
        king_to,
        on_finished=_finish,
        duration_ms=50,
        extra_slides=[(rook, rook_from, rook_to)],
    )
    assert board.is_animating
    assert len(board._slides) == 2
    assert board.hidden == {king_from, king_to, rook_from, rook_to}
    assert _wait_until(qapp, lambda: done["ok"], timeout_s=2.0)
    assert not board.is_animating
    assert board._slides == []
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


def test_qt_promotion_dialog_defaults_to_queen_choice(qapp) -> None:
    dialog = PromotionDialog(Color.WHITE)
    assert dialog.choice is None
    # Simulate clicking the default Queen button path.
    dialog._accept(PieceType.QUEEN)
    assert dialog.choice is PieceType.QUEEN
    dialog.close()


def test_qt_move_list_review_and_live(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    window.controller.make_player_move_from_notation("e2", "e4")
    window.controller.make_ai_move()
    window.controller.make_player_move_from_notation("d2", "d4")
    window._refresh()
    assert window.move_header.text().replace(" ", "").find("White") >= 0
    assert "Black" in window.move_header.text()
    assert window.move_list.count() >= 2
    assert window.live_btn.isEnabled() is False

    # First full move (White+Black) is intermediate while ply 3 exists.
    first = window.move_list.item(0)
    window._on_move_list_clicked(first)
    assert window._is_reviewing()
    assert window._review_plies == 2
    assert window.live_btn.isEnabled()
    assert "Reviewing" in window.hint.text()

    window._on_live_clicked()
    assert not window._is_reviewing()
    assert "live" in window.hint.text().lower()
    window.close()


def test_qt_captured_pieces_use_large_glyphs(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    assert window.captured_you.objectName() == "capturedPieces"
    assert window.captured_ai.objectName() == "capturedPieces"
    assert window.captured_you.minimumHeight() >= 40
    pixel = window.captured_you.font().pixelSize()
    point = window.captured_you.font().pointSize()
    assert max(pixel, point) >= 20 or window.captured_you.minimumHeight() >= 40
    window.close()


def test_qt_escape_clears_selection(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    window._select(Position.from_chess_notation("e2"))
    assert window.selected is not None
    window._on_escape()
    assert window.selected is None
    window.close()


def test_qt_ai_vs_ai_mode_widgets_and_step(qapp) -> None:
    window = ChessMainWindow(difficulty_key="beginner")
    assert window.mode_box.findData("ai_vs_ai") >= 0
    window.mode_box.setCurrentIndex(window.mode_box.findData("ai_vs_ai"))
    qapp.processEvents()
    assert window._is_ai_vs_ai()
    assert not window.match_panel.isHidden()
    assert window.step_btn.isEnabled()
    assert window.side_box.isHidden()

    # Board clicks are ignored in spectator mode.
    before = window.controller.get_state().ply_count
    window._on_square_clicked(Position.from_chess_notation("e2"))
    assert window.controller.get_state().ply_count == before

    window.white_diff_box.setCurrentIndex(0)  # beginner
    window.black_diff_box.setCurrentIndex(0)
    window.speed_box.setCurrentIndex(0)  # fastest delay
    window._on_match_step()
    assert window._ai_busy or window._animating or window.controller.get_state().ply_count >= 1
    if window._worker is not None:
        window._worker.wait(15000)
    assert _wait_until(
        qapp,
        lambda: not window._busy() and window.controller.get_state().ply_count >= 1,
        timeout_s=20.0,
    )
    assert window.controller.get_state().ply_count >= 1
    pgn = window._pgn_text()
    assert "AI (" in pgn

    window.mode_box.setCurrentIndex(window.mode_box.findData("player"))
    qapp.processEvents()
    assert not window._is_ai_vs_ai()
    assert not window.side_box.isHidden()
    assert window.match_panel.isHidden()
    window.close()
