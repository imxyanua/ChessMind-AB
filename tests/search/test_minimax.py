"""Unit tests for MinimaxSearch on small tactical fixtures."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.minimax import MinimaxSearch


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


def test_minimax_captures_hanging_queen() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e4": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "e2": Piece(type=PieceType.ROOK, color=Color.WHITE),
        }
    )
    result = MinimaxSearch().find_best_move(state, depth=1)
    assert result.best_move is not None
    assert result.best_move.from_position.to_chess_notation() == "e2"
    assert result.best_move.to_position.to_chess_notation() == "e4"
    assert result.best_move.captured_piece is not None
    assert result.best_move.captured_piece.type is PieceType.QUEEN


def test_minimax_finds_back_rank_mate_in_one() -> None:
    # h-file is open so Rh4-h8# is available.
    state = _state(
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
    )
    result = MinimaxSearch().find_best_move(state, depth=1)
    assert result.best_move is not None
    assert result.best_move.from_position.to_chess_notation() == "h4"
    assert result.best_move.to_position.to_chess_notation() == "h8"
    assert result.best_score > 50_000


def test_cancel_stops_search_without_crash() -> None:
    search = MinimaxSearch(use_quiescence=False)
    search.cancel()
    result = search.find_best_move(create_initial_game_state(), depth=1)
    assert result.best_move is not None
