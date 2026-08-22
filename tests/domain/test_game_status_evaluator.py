"""Unit tests for GameStatusEvaluator (P2-4)."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def _state(pieces: dict[str, Piece], side: Color) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=side,
        status=GameStatus.ONGOING,
        ply_count=10,
    )


def test_ongoing_when_legal_moves_exist() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        },
        Color.WHITE,
    )
    assert GameStatusEvaluator.evaluate(state) is GameStatus.ONGOING


def test_back_rank_mate_white_to_move() -> None:
    # Classic back-rank style: white king trapped on back rank by black rook.
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a1": Piece(type=PieceType.ROOK, color=Color.BLACK),
            "a2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "b2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "c2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "d2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "e2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "f2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "g2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "h2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        },
        Color.WHITE,
    )
    assert GameStatusEvaluator.evaluate(state) is GameStatus.BLACK_WINS_CHECKMATE


def test_stalemate_when_no_legal_move_and_not_in_check() -> None:
    # Black king in corner, white queen takes all escapes but does not check.
    state = _state(
        {
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "b6": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "c7": Piece(type=PieceType.KING, color=Color.WHITE),
        },
        Color.BLACK,
    )
    assert GameStatusEvaluator.evaluate(state) is GameStatus.STALEMATE
