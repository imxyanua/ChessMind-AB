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
        choices=["gui", "demo", "play"],
        help="gui = graphical window (default); demo/play = terminal helpers",
    )
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args(argv)

    if args.command == "gui":
        from chessmind_ab.presentation.gui import run_gui

        run_gui(depth=args.depth)
        return 0

    if args.command == "demo":
        print(run_demo(depth=args.depth))
        return 0

    controller = GameController(ai_depth=args.depth)
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
