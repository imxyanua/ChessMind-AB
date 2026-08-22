"""Unit tests for MoveOrdering."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.minimax import MinimaxSearch
from chessmind_ab.search.move_ordering import MoveOrdering


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


def test_ordering_preserves_move_set() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e7": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "d8": Piece(type=PieceType.KNIGHT, color=Color.BLACK),
            "a2": Piece(type=PieceType.ROOK, color=Color.WHITE),
        }
    )
    moves = LegalMoveGenerator.generate(state)
    ordered = MoveOrdering.order(state, moves)
    assert len(ordered) == len(moves)
    assert set(ordered) == set(moves)


def test_ordering_priority_promotion_then_capture_then_normal() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e7": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "d8": Piece(type=PieceType.ROOK, color=Color.BLACK),
            "a2": Piece(type=PieceType.ROOK, color=Color.WHITE),
        }
    )
    ordered = MoveOrdering.order(state, LegalMoveGenerator.generate(state))
    priorities = []
    for move in ordered:
        if move.move_type in {MoveType.PROMOTION, MoveType.PROMOTION_CAPTURE}:
            priorities.append(0)
        elif move.move_type is MoveType.CAPTURE:
            priorities.append(1)
        else:
            priorities.append(2)
    assert priorities == sorted(priorities)


def test_ordered_alpha_beta_matches_minimax_score() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "h8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        }
    )
    mini = MinimaxSearch().find_best_move(state, depth=2)
    ordered_ab = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(
        state, depth=2
    )
    assert ordered_ab.best_score == mini.best_score
