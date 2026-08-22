"""Small deterministic benchmark comparing Minimax and Alpha-Beta."""

from __future__ import annotations

from dataclasses import dataclass

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.minimax import MinimaxSearch
from chessmind_ab.search.move_ordering import MoveOrdering


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


def _fixture() -> GameState:
    board = Board()
    pieces = {
        "e1": Piece(type=PieceType.KING, color=Color.WHITE),
        "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
        "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
        "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
        "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        "c3": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
        "c6": Piece(type=PieceType.KNIGHT, color=Color.BLACK),
    }
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def run_benchmark(depth: int = 2) -> list[BenchmarkRow]:
    state = _fixture()
    algorithms = [
        ("Minimax", MinimaxSearch()),
        ("AlphaBeta", AlphaBetaSearch()),
        ("AlphaBeta+Ordering", AlphaBetaSearch(move_ordering=MoveOrdering())),
    ]
    rows: list[BenchmarkRow] = []
    for name, algorithm in algorithms:
        result = algorithm.find_best_move(state, depth)
        best = "none"
        if result.best_move is not None:
            best = (
                result.best_move.from_position.to_chess_notation()
                + result.best_move.to_position.to_chess_notation()
            )
        rows.append(
            BenchmarkRow(
                name="T3-mid",
                algorithm=name,
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
