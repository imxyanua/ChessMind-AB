"""Unit tests for EvaluationFunction V1."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.evaluation import EvaluationFunction


def _state(pieces: dict[str, Piece]) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_equal_material_is_zero() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
        }
    )
    assert EvaluationFunction.evaluate(state) == 0


def test_white_extra_queen_scores_plus_900() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
        }
    )
    assert EvaluationFunction.evaluate(state) == 900


def test_black_extra_rook_scores_minus_500() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        }
    )
    assert EvaluationFunction.evaluate(state) == -500
