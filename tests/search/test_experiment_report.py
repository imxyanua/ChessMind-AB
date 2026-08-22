"""Tests for experimental report analysis and writers."""

from pathlib import Path

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.benchmark import BenchmarkRow, run_benchmark
from chessmind_ab.search.experiment_report import (
    analyze_hypotheses,
    build_report,
    render_markdown,
    write_report,
)


def _tiny() -> GameState:
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    board.set_piece(
        Position.from_chess_notation("d1"),
        Piece(type=PieceType.QUEEN, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("d8"),
        Piece(type=PieceType.QUEEN, color=Color.BLACK),
    )
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_analyze_hypotheses_h1_h2_on_tiny_suite() -> None:
    rows = run_benchmark(depth=1, positions={"T": _tiny()})
    results = {item.key: item for item in analyze_hypotheses(rows)}
    assert results["H1"].supported is True
    assert results["H2"].supported is True
    assert "H3" in results
    assert results["H4"].supported is None  # single depth


def test_render_markdown_contains_sections() -> None:
    rows = [
        BenchmarkRow("T", "Minimax", 1, 100, 0, 10, "d1d8", 1.0),
        BenchmarkRow("T", "AlphaBeta", 1, 40, 5, 10, "d1d8", 0.5),
        BenchmarkRow("T", "AlphaBeta+Ordering", 1, 30, 8, 10, "d1d8", 0.4),
        BenchmarkRow("T", "Minimax", 2, 400, 0, 12, "d1d8", 4.0),
        BenchmarkRow("T", "AlphaBeta", 2, 80, 20, 12, "d1d8", 1.0),
        BenchmarkRow("T", "AlphaBeta+Ordering", 2, 60, 25, 12, "d1d8", 0.8),
    ]
    hyps = analyze_hypotheses(rows)
    md = render_markdown(rows, hyps)
    assert "# ChessMind-AB Experimental Report" in md
    assert "### H1" in md
    assert "### H5" in md
    assert "SUPPORTED" in md
    assert "| T | Minimax | 1 |" in md


def test_write_report_creates_csv_and_markdown(tmp_path: Path) -> None:
    # Monkeypatch via tiny suite by calling build pieces through write_report
    # on real suite would be slow; use build_report depths=[1] then write manually.
    report = build_report(depths=[1])
    assert len(report.rows) == 15  # 5 positions x 3 algorithms
    assert any(h.key == "H1" for h in report.hypotheses)

    csv_path, md_path, written = write_report(tmp_path, depths=[1])
    assert csv_path.exists()
    assert md_path.exists()
    assert "position,algorithm,depth,nodes" in csv_path.read_text(encoding="utf-8")
    assert "Hypothesis results" in md_path.read_text(encoding="utf-8")
    assert written.hypotheses[0].key == "H1"
