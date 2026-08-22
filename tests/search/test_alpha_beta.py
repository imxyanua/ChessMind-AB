"""Alpha-Beta correctness and equivalence with Minimax."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
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


def _hanging_queen_state() -> GameState:
    return _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e4": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            "e2": Piece(type=PieceType.ROOK, color=Color.WHITE),
        }
    )


def _mate_in_one_state() -> GameState:
    return _state(
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


def _open_ish_state() -> GameState:
    return _state(
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
    )


def test_alpha_beta_matches_minimax_score_and_move_on_fixtures() -> None:
    fixtures = [_hanging_queen_state(), _mate_in_one_state(), _open_ish_state()]
    for state in fixtures:
        for depth in (1, 2):
            mini = MinimaxSearch().find_best_move(state, depth)
            ab = AlphaBetaSearch().find_best_move(state, depth)
            assert ab.best_score == mini.best_score
            assert ab.best_move == mini.best_move


def test_alpha_beta_can_record_cutoffs_on_deeper_search() -> None:
    result = AlphaBetaSearch().find_best_move(_open_ish_state(), depth=2)
    assert result.statistics.nodes_visited > 0
    assert result.statistics.cutoffs >= 0
