"""Unit tests for strengthened MoveOrdering."""

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


def test_mvv_lva_prefers_capturing_queen_over_pawn() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d4": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
            "e6": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "c6": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    ordered = MoveOrdering.order(state, LegalMoveGenerator.generate(state))
    captures = [m for m in ordered if m.move_type is MoveType.CAPTURE]
    assert captures
    assert captures[0].to_position.to_chess_notation() == "e6"
    assert captures[0].captured_piece is not None
    assert captures[0].captured_piece.type is PieceType.QUEEN


def test_checking_move_outranks_quiet_non_capture() -> None:
    # White rook can check on open file or move sideways quietly.
    state = _state(
        {
            "a1": Piece(type=PieceType.KING, color=Color.WHITE),
            "h1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "b7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "c7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "d7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "e7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "f7": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "g7": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    ordered = MoveOrdering.order(state, LegalMoveGenerator.generate(state))
    # First non-capture should include the checking rook lift/file if present.
    non_captures = [
        m
        for m in ordered
        if m.move_type not in {MoveType.CAPTURE, MoveType.PROMOTION, MoveType.PROMOTION_CAPTURE}
    ]
    assert non_captures
    assert non_captures[0].to_position.to_chess_notation() == "h8"


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
