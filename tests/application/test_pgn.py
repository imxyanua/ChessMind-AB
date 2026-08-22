"""Tests for SAN formatting and PGN export."""

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.application.pgn import build_pgn, format_san, result_token
from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


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


def _move(state: GameState, from_sq: str, to_sq: str):
    source = Position.from_chess_notation(from_sq)
    target = Position.from_chess_notation(to_sq)
    for move in LegalMoveGenerator.generate(state):
        if move.from_position == source and move.to_position == target:
            return move
    raise AssertionError(f"No legal move {from_sq}{to_sq}")


def test_format_san_quiet_pawn_and_knight() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    controller.make_player_move_from_notation("e2", "e4")
    history = controller.get_move_history()
    assert history[0].notation == "e4"


def test_format_san_capture_and_check() -> None:
    state = _state(
        {
            "e1": Piece(PieceType.KING, Color.WHITE),
            "e8": Piece(PieceType.KING, Color.BLACK),
            "h5": Piece(PieceType.QUEEN, Color.WHITE),
            "e5": Piece(PieceType.PAWN, Color.BLACK),
        }
    )
    move = _move(state, "h5", "e5")
    assert format_san(state, move) == "Qxe5+"


def test_format_san_disambiguation_by_file() -> None:
    state = _state(
        {
            "e1": Piece(PieceType.KING, Color.WHITE),
            "e8": Piece(PieceType.KING, Color.BLACK),
            "a4": Piece(PieceType.KNIGHT, Color.WHITE),
            "c4": Piece(PieceType.KNIGHT, Color.WHITE),
        }
    )
    move = _move(state, "a4", "b6")
    assert format_san(state, move) == "Nab6"


def test_build_pgn_headers_and_moves() -> None:
    text = build_pgn(["e4", "e5", "Nf3"], GameStatus.ONGOING)
    assert '[Event "ChessMind-AB Game"]' in text
    assert '[Result "*"]' in text
    assert "1. e4 e5 2. Nf3 *" in text


def test_result_token_mapping() -> None:
    assert result_token(GameStatus.ONGOING) == "*"
    assert result_token(GameStatus.WHITE_WINS_CHECKMATE) == "1-0"
    assert result_token(GameStatus.BLACK_WINS_CHECKMATE) == "0-1"
    assert result_token(GameStatus.STALEMATE) == "1/2-1/2"


def test_controller_to_pgn_after_turns() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    controller.make_player_move_from_notation("e2", "e4")
    controller.make_ai_move()
    pgn = controller.to_pgn()
    assert '[White "Player"]' in pgn
    assert '[Black "ChessMind-AB"]' in pgn
    assert "1. e4 " in pgn
    assert pgn.strip().endswith("*")
    assert controller.can_undo()
    controller.undo()
    assert controller.get_move_history() == []
    undone_pgn = controller.to_pgn()
    assert undone_pgn.strip().endswith("*")
    assert "1. e4" not in undone_pgn
