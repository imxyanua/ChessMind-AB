"""Exercise the non-interactive Player-vs-AI demo entrypoint."""

from chessmind_ab.presentation.cli import run_demo
from chessmind_ab.search.benchmark import format_benchmark, run_benchmark


def test_run_demo_produces_board_and_ai_move() -> None:
    output = run_demo(depth=1, plies=2)
    assert "side=" in output
    assert "demo: player e2e4" in output
    assert "player_result=True" in output
    assert "ai_move=" in output


def test_benchmark_rows_compare_algorithms() -> None:
    rows = run_benchmark(depth=1)
    assert len(rows) == 3
    scores = {row.score for row in rows}
    assert len(scores) == 1
    text = format_benchmark(rows)
    assert "Minimax" in text
    assert "AlphaBeta" in text
