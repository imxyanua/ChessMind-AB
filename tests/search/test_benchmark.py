"""Benchmark harness tests (fast depth=1 suite subset)."""

from pathlib import Path

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.benchmark import (
    format_benchmark,
    format_benchmark_table,
    run_benchmark,
    write_benchmark_csv,
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


def test_run_benchmark_emits_three_algorithms() -> None:
    rows = run_benchmark(depth=1, positions={"T": _tiny()})
    assert len(rows) == 3
    assert {row.algorithm for row in rows} == {
        "Minimax",
        "AlphaBeta",
        "AlphaBeta+Ordering",
    }
    assert len({row.score for row in rows}) == 1


def test_write_benchmark_csv(tmp_path: Path) -> None:
    rows = run_benchmark(depth=1, positions={"T": _tiny()})
    path = write_benchmark_csv(rows, tmp_path / "out.csv")
    text = path.read_text(encoding="utf-8")
    assert "position,algorithm,depth,nodes" in text
    assert "Minimax" in text
    assert format_benchmark(rows).splitlines()[0] in text
    assert "Nodes" in format_benchmark_table(rows)
