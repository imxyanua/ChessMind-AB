"""Unit tests for EvaluationFunction V2 (material + PST + mobility + king safety)."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.evaluation import EvaluationFunction, king_safety_score


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


def test_evaluate_initial_position_and_kings_only_does_not_crash() -> None:
    from chessmind_ab.domain.initial_position import create_initial_game_state

    initial = create_initial_game_state()
    assert isinstance(EvaluationFunction.evaluate(initial), int)

    kings_only = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    assert isinstance(EvaluationFunction.evaluate(kings_only), int)


def test_higher_mobility_side_scores_better_with_equal_material() -> None:
    cramped = _state(
        {
            "a1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "b1": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "h8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d5": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        }
    )
    # Give white matching material but more open lines.
    open_white = _state(
        {
            "a1": Piece(type=PieceType.KING, color=Color.WHITE),
            "d4": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "h1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "h8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "b7": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    assert EvaluationFunction.evaluate(open_white) > EvaluationFunction.evaluate(cramped)


def test_pawn_shield_improves_king_safety() -> None:
    bare = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    shielded = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "d2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "e2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "f2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    assert king_safety_score(shielded) > king_safety_score(bare)
    assert EvaluationFunction.evaluate(shielded) > EvaluationFunction.evaluate(bare)


def test_enemy_queen_near_king_worsens_safety() -> None:
    safe = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
        }
    )
    pressured = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e3": Piece(type=PieceType.QUEEN, color=Color.BLACK),
        }
    )
    assert king_safety_score(pressured) < king_safety_score(safe)
    assert EvaluationFunction.evaluate(pressured) < EvaluationFunction.evaluate(safe)
