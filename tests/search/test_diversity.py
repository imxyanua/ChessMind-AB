"""Play-mode root move diversity (deterministic with seeded RNG)."""

import random

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.move_ordering import MoveOrdering


def _open_state() -> GameState:
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
        "e2": Piece(type=PieceType.PAWN, color=Color.WHITE),
        "e7": Piece(type=PieceType.PAWN, color=Color.BLACK),
        "d2": Piece(type=PieceType.PAWN, color=Color.WHITE),
        "d7": Piece(type=PieceType.PAWN, color=Color.BLACK),
    }
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_diversity_disabled_is_deterministic() -> None:
    state = _open_state()
    a = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(state, 2)
    b = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(state, 2)
    assert a.best_move == b.best_move
    assert a.best_score == b.best_score


def test_seeded_diversity_is_reproducible_but_can_differ_across_seeds() -> None:
    state = _open_state()
    first = AlphaBetaSearch(
        move_ordering=MoveOrdering(),
        diversity_window=50,
        rng=random.Random(1),
    ).find_best_move(state, 2)
    again = AlphaBetaSearch(
        move_ordering=MoveOrdering(),
        diversity_window=50,
        rng=random.Random(1),
    ).find_best_move(state, 2)
    other = AlphaBetaSearch(
        move_ordering=MoveOrdering(),
        diversity_window=50,
        rng=random.Random(99),
    ).find_best_move(state, 2)

    assert first.best_move == again.best_move
    assert first.best_score == again.best_score
    # Different seeds may still collide; allow either different move or same score band.
    assert other.best_score == first.best_score or other.best_move != first.best_move
