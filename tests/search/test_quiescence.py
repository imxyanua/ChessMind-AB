"""Quiescence search reduces horizon-effect blunders."""

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
from chessmind_ab.search.quiescence import tactical_moves


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


def test_tactical_moves_are_captures_or_promotions_only() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e2": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "e4": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "a2": Piece(type=PieceType.PAWN, color=Color.WHITE),
        }
    )
    moves = tactical_moves(state)
    assert moves
    assert all(
        move.captured_piece is not None or move.promotion_piece is not None
        for move in moves
    )


def test_quiescence_avoids_queen_takes_protected_knight() -> None:
    """Depth-1 leaf would see +N, but quiescence sees rook recapture of the queen."""
    state = _state(
        {
            "h1": Piece(type=PieceType.KING, color=Color.WHITE),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e5": Piece(type=PieceType.KNIGHT, color=Color.BLACK),
            "e8": Piece(type=PieceType.ROOK, color=Color.BLACK),
            "a2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "h7": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    result = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(state, depth=1)
    assert result.best_move is not None
    # Must not play Qxe5 (queen from d1 to e5).
    assert not (
        result.best_move.from_position.to_chess_notation() == "d1"
        and result.best_move.to_position.to_chess_notation() == "e5"
    )


def test_minimax_and_alphabeta_still_match_with_quiescence() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "a8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        }
    )
    mini = MinimaxSearch().find_best_move(state, depth=1)
    ab = AlphaBetaSearch().find_best_move(state, depth=1)
    assert mini.best_score == ab.best_score
    assert mini.best_move == ab.best_move
