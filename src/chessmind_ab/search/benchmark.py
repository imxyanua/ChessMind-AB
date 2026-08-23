"""Deterministic benchmark comparing Minimax and Alpha-Beta variants."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.minimax import MinimaxSearch
from chessmind_ab.search.move_ordering import MoveOrdering
from chessmind_ab.search.transposition_table import TranspositionTable


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    name: str
    algorithm: str
    depth: int
    nodes: int
    cutoffs: int
    score: int
    best_move: str
    time_ms: float


def _state(pieces: dict[str, Piece], side: Color = Color.WHITE) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=side,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def benchmark_positions() -> dict[str, GameState]:
    return {
        "T1-opening": create_initial_game_state(),
        "T2-open": _state(
            {
                "e1": Piece(type=PieceType.KING, color=Color.WHITE),
                "e8": Piece(type=PieceType.KING, color=Color.BLACK),
                "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
                "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
                "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
                "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
                "c1": Piece(type=PieceType.BISHOP, color=Color.WHITE),
                "c8": Piece(type=PieceType.BISHOP, color=Color.BLACK),
                "b1": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
                "b8": Piece(type=PieceType.KNIGHT, color=Color.BLACK),
            }
        ),
        "T3-mid": _state(
            {
                "e1": Piece(type=PieceType.KING, color=Color.WHITE),
                "e8": Piece(type=PieceType.KING, color=Color.BLACK),
                "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
                "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
                "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
                "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
                "c3": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
                "c6": Piece(type=PieceType.KNIGHT, color=Color.BLACK),
            }
        ),
        "T4-endgame": _state(
            {
                "e1": Piece(type=PieceType.KING, color=Color.WHITE),
                "e8": Piece(type=PieceType.KING, color=Color.BLACK),
                "a4": Piece(type=PieceType.ROOK, color=Color.WHITE),
                "h5": Piece(type=PieceType.ROOK, color=Color.BLACK),
                "e4": Piece(type=PieceType.PAWN, color=Color.WHITE),
                "e5": Piece(type=PieceType.PAWN, color=Color.BLACK),
            }
        ),
        "T5-mate": _state(
            {
                "e1": Piece(type=PieceType.KING, color=Color.WHITE),
                "h4": Piece(type=PieceType.ROOK, color=Color.WHITE),
                "e8": Piece(type=PieceType.KING, color=Color.BLACK),
                "a7": Piece(type=PieceType.PAWN, color=Color.BLACK),
                "b7": Piece(type=PieceType.PAWN, color=Color.BLACK),
                "c7": Piece(type=PieceType.PAWN, color=Color.BLACK),
                "d7": Piece(type=PieceType.PAWN, color=Color.BLACK),
                "e7": Piece(type=PieceType.PAWN, color=Color.BLACK),
                "f7": Piece(type=PieceType.PAWN, color=Color.BLACK),
                "g7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            }
        ),
    }


def _algorithms(*, with_tt: bool = False):
    # Deterministic: no diversity RNG for fair comparison.
    algorithms = [
        ("Minimax", MinimaxSearch()),
        ("AlphaBeta", AlphaBetaSearch()),
        ("AlphaBeta+Ordering", AlphaBetaSearch(move_ordering=MoveOrdering())),
    ]
    if with_tt:
        algorithms.append(
            (
                "AlphaBeta+Ordering+TT",
                AlphaBetaSearch(
                    move_ordering=MoveOrdering(),
                    transposition_table=TranspositionTable(size_power=16),
                ),
            )
        )
    return algorithms


def run_benchmark(
    depth: int = 2,
    positions: dict[str, GameState] | None = None,
    *,
    with_tt: bool = False,
) -> list[BenchmarkRow]:
    suite = positions or benchmark_positions()
    rows: list[BenchmarkRow] = []
    for pos_name, state in suite.items():
        for algo_name, algorithm in _algorithms(with_tt=with_tt):
            result = algorithm.find_best_move(state, depth)
            best = "none"
            if result.best_move is not None:
                best = (
                    result.best_move.from_position.to_chess_notation()
                    + result.best_move.to_position.to_chess_notation()
                )
            rows.append(
                BenchmarkRow(
                    name=pos_name,
                    algorithm=algo_name,
                    depth=depth,
                    nodes=result.statistics.nodes_visited,
                    cutoffs=result.statistics.cutoffs,
                    score=result.best_score,
                    best_move=best,
                    time_ms=result.statistics.execution_time_ms,
                )
            )
    return rows


def format_benchmark(rows: list[BenchmarkRow]) -> str:
    lines = [
        "position,algorithm,depth,nodes,cutoffs,score,best_move,time_ms",
    ]
    for row in rows:
        lines.append(
            f"{row.name},{row.algorithm},{row.depth},{row.nodes},"
            f"{row.cutoffs},{row.score},{row.best_move},{row.time_ms:.2f}"
        )
    return "\n".join(lines)


def format_benchmark_table(rows: list[BenchmarkRow]) -> str:
    header = (
        f"{'Position':<12} {'Algorithm':<20} {'Depth':>5} "
        f"{'Nodes':>8} {'Cutoffs':>8} {'Score':>8} {'Move':<8} {'TimeMs':>8}"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row.name:<12} {row.algorithm:<20} {row.depth:>5} "
            f"{row.nodes:>8} {row.cutoffs:>8} {row.score:>8} "
            f"{row.best_move:<8} {row.time_ms:>8.1f}"
        )
    return "\n".join(lines)


def write_benchmark_csv(rows: list[BenchmarkRow], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_benchmark(rows) + "\n", encoding="utf-8")
    return path
