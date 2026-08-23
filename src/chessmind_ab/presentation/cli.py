"""Console UI for Player vs AI and a non-interactive demo mode."""

from __future__ import annotations

import argparse

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def _symbol(piece: Piece | None) -> str:
    if piece is None:
        return "."
    mapping = {
        PieceType.PAWN: "P",
        PieceType.KNIGHT: "N",
        PieceType.BISHOP: "B",
        PieceType.ROOK: "R",
        PieceType.QUEEN: "Q",
        PieceType.KING: "K",
    }
    letter = mapping[piece.type]
    return letter if piece.color is Color.WHITE else letter.lower()


def render_board(controller: GameController) -> str:
    state = controller.get_state()
    lines = ["  a b c d e f g h"]
    for row in range(8):
        rank = 8 - row
        cells = []
        for column in range(8):
            piece = state.board.get_piece(Position(row=row, column=column))
            cells.append(_symbol(piece))
        lines.append(f"{rank} " + " ".join(cells))
    lines.append(f"side={state.side_to_move.name} status={state.status.name} ply={state.ply_count}")
    return "\n".join(lines)


def run_demo(depth: int = 1, plies: int = 4) -> str:
    """Non-interactive Player-vs-AI smoke path used for verification."""
    controller = GameController(ai_depth=depth, player_color=Color.WHITE)
    controller.start_new_game()
    output = [render_board(controller), "demo: player e2e4"]
    result = controller.make_player_move_from_notation("e2", "e4")
    output.append(f"player_result={result.success} {result.message}")
    output.append(render_board(controller))

    for index in range(plies):
        if controller.get_state().status is not GameStatus.ONGOING:
            break
        if controller.get_state().side_to_move is Color.WHITE:
            legal = controller.get_legal_moves()
            if not legal:
                break
            move = legal[0]
            result = controller.make_player_move(move)
            output.append(
                f"auto_player={move.from_position.to_chess_notation()}"
                f"{move.to_position.to_chess_notation()} ok={result.success}"
            )
        else:
            result = controller.make_ai_move()
            search = controller.get_last_search_result()
            move_txt = "none"
            if search and search.best_move is not None:
                move_txt = (
                    search.best_move.from_position.to_chess_notation()
                    + search.best_move.to_position.to_chess_notation()
                )
            output.append(f"ai_move={move_txt} ok={result.success} ply={index}")
        output.append(render_board(controller))
    return "\n".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chessmind-ab")
    parser.add_argument(
        "command",
        nargs="?",
        default="gui",
        choices=["gui", "demo", "play", "benchmark", "report"],
        help="gui/demo/play/benchmark/report",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="medium",
        choices=["beginner", "easy", "medium", "hard", "expert"],
        help="GUI/play difficulty preset (Elo mode)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Optional search depth override (benchmark/demo/play)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="benchmark_results.csv",
        help="CSV output path for benchmark command",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="experiment_out",
        help="Output directory for report command (CSV + Markdown)",
    )
    parser.add_argument(
        "--depths",
        type=str,
        default="1,2",
        help="Comma-separated depths for report command (default: 1,2)",
    )
    parser.add_argument(
        "--debug-search",
        action="store_true",
        help="Enable Alpha-Beta debug logging (depth/move/alpha/beta/score/cutoff)",
    )
    parser.add_argument(
        "--tt",
        action="store_true",
        help="Include AlphaBeta+Ordering+TT in benchmark comparison",
    )
    args = parser.parse_args(argv)

    from chessmind_ab.search.debug_log import configure_from_env, set_debug_search

    configure_from_env()
    if args.debug_search:
        set_debug_search(True)

    if args.command == "gui":
        from chessmind_ab.presentation.gui import run_gui

        run_gui(depth=args.depth, difficulty=args.difficulty)
        return 0

    if args.command == "demo":
        print(run_demo(depth=args.depth or 1))
        return 0

    if args.command == "benchmark":
        from pathlib import Path

        from chessmind_ab.search.benchmark import (
            format_benchmark_table,
            run_benchmark,
            write_benchmark_csv,
        )

        # Benchmarks stay quiet even if env enabled debug logging.
        set_debug_search(False)
        # Keep experimental runs practical; depth 1-2 recommended.
        depth = args.depth if args.depth is not None and args.depth >= 1 else 1
        rows = run_benchmark(depth=depth, with_tt=args.tt)
        print(format_benchmark_table(rows))
        out = write_benchmark_csv(rows, Path(args.out))
        print(f"\nWrote CSV: {out.resolve()}")
        return 0

    if args.command == "report":
        from pathlib import Path

        from chessmind_ab.search.experiment_report import write_report

        set_debug_search(False)
        depths = [int(part.strip()) for part in args.depths.split(",") if part.strip()]
        if args.depth is not None:
            depths = [args.depth]
        csv_path, md_path, report = write_report(Path(args.report_dir), depths=depths)
        print(f"Wrote CSV: {csv_path.resolve()}")
        print(f"Wrote Markdown: {md_path.resolve()}")
        for hyp in report.hypotheses:
            verdict = (
                "SUPPORTED"
                if hyp.supported is True
                else "NOT SUPPORTED"
                if hyp.supported is False
                else "INCONCLUSIVE"
            )
            print(f"{hyp.key}: {verdict} — {hyp.detail}")
        return 0

    controller = GameController(
        difficulty_key=args.difficulty,
        ai_depth=args.depth,
    )
    controller.start_new_game()
    print(render_board(controller))
    print("Enter moves like e2e4, or 'quit'.")
    while controller.get_state().status is GameStatus.ONGOING:
        if controller.get_state().side_to_move is Color.WHITE:
            raw = input("> ").strip().lower()
            if raw in {"q", "quit", "exit"}:
                break
            if len(raw) != 4:
                print("Invalid format")
                continue
            result = controller.make_player_move_from_notation(raw[:2], raw[2:])
            print(result.message)
            print(render_board(controller))
        else:
            result = controller.make_ai_move()
            search = controller.get_last_search_result()
            if search and search.best_move is not None:
                print(
                    "AI:",
                    search.best_move.from_position.to_chess_notation()
                    + search.best_move.to_position.to_chess_notation(),
                    "score=",
                    search.best_score,
                )
            print(result.message)
            print(render_board(controller))
    print("Done:", controller.get_state().status.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
