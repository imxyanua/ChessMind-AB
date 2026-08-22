"""Unit tests for EvaluationFunction V2 (material + PST)."""

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


def test_mirrored_equal_material_is_zero() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
        }
    )
    assert EvaluationFunction.evaluate(state) == 0


def test_white_extra_queen_is_strongly_positive() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
        }
    )
    assert EvaluationFunction.evaluate(state) >= 850


def test_black_extra_rook_is_strongly_negative() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        }
    )
    assert EvaluationFunction.evaluate(state) <= -450


def test_central_knight_better_than_rim_knight() -> None:
    rim = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a1": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
        }
    )
    center = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e4": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
        }
    )
    assert EvaluationFunction.evaluate(center) > EvaluationFunction.evaluate(rim)
