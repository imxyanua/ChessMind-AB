"""Unit tests for GameController."""

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def test_start_new_game_has_initial_setup() -> None:
    controller = GameController()
    state = controller.start_new_game()
    assert state.side_to_move is Color.WHITE
    assert state.status is GameStatus.ONGOING
    assert state.ply_count == 0
    assert len(controller.get_legal_moves()) > 0


def test_checked_king_position_when_in_check() -> None:
    controller = GameController(ai_depth=1)
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    board.set_piece(
        Position.from_chess_notation("e2"),
        Piece(type=PieceType.ROOK, color=Color.BLACK),
    )
    state = GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=1,
    )
    square = controller.checked_king_position(state)
    assert square == Position.from_chess_notation("e1")


def test_invalid_player_move_is_rejected() -> None:
    controller = GameController()
    controller.start_new_game()
    result = controller.make_player_move_from_notation("e2", "e5")
    assert result.success is False
    assert "Illegal" in result.message
    assert controller.get_state().ply_count == 0


def test_player_then_ai_turn_advances() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    player = controller.make_player_move_from_notation("e2", "e4")
    assert player.success is True
    assert controller.get_state().side_to_move is Color.BLACK
    ai = controller.make_ai_move()
    assert ai.success is True
    assert controller.get_state().side_to_move is Color.WHITE
    assert controller.get_last_search_result() is not None
    assert len(controller.get_move_history()) == 2


def test_undo_restores_previous_turn() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    controller.make_player_move_from_notation("e2", "e4")
    controller.make_ai_move()
    assert controller.can_undo()
    undone = controller.undo()
    assert undone.success is True
    assert controller.get_state().ply_count == 0
    assert controller.get_move_history() == []


def test_play_as_black_ai_moves_first_as_white() -> None:
    controller = GameController(ai_depth=1, player_color=Color.BLACK)
    controller.start_new_game()
    assert controller.get_player_color() is Color.BLACK
    assert controller.get_state().side_to_move is Color.WHITE
    ai = controller.make_ai_move()
    assert ai.success is True
    assert controller.get_state().side_to_move is Color.BLACK
    pgn = controller.to_pgn()
    assert '[White "ChessMind-AB"]' in pgn
    assert '[Black "Player"]' in pgn


def test_make_ai_move_rejects_on_player_turn() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    result = controller.make_ai_move()
    assert result.success is False
    assert "Not AI turn" in result.message


def test_make_engine_move_plays_both_sides_for_ai_vs_ai() -> None:
    from chessmind_ab.application.difficulty import get_difficulty

    controller = GameController(ai_depth=1, player_color=Color.WHITE)
    controller.start_new_game()
    beginner = get_difficulty("beginner")
    easy = get_difficulty("easy")

    white = controller.make_engine_move(difficulty=beginner, push_undo=True)
    assert white.success is True
    assert controller.get_state().side_to_move is Color.BLACK
    assert controller.can_undo()

    black = controller.make_engine_move(difficulty=easy, push_undo=True)
    assert black.success is True
    assert controller.get_state().side_to_move is Color.WHITE
    assert len(controller.get_move_history()) == 2

    undone = controller.undo()
    assert undone.success is True
    assert controller.get_state().side_to_move is Color.BLACK
    assert len(controller.get_move_history()) == 1

    pgn = controller.to_pgn(white="AI (Beginner)", black="AI (Easy)")
    assert '[White "AI (Beginner)"]' in pgn
    assert '[Black "AI (Easy)"]' in pgn


def _promotion_ready_controller() -> GameController:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    board = Board()
    board.set_piece(
        Position.from_chess_notation("e7"),
        Piece(type=PieceType.PAWN, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("e1"),
        Piece(type=PieceType.KING, color=Color.WHITE),
    )
    board.set_piece(
        Position.from_chess_notation("a8"),
        Piece(type=PieceType.KING, color=Color.BLACK),
    )
    controller._state = GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=20,
    )
    return controller


def test_player_promotion_defaults_to_queen() -> None:
    controller = _promotion_ready_controller()
    candidates = controller.find_move_candidates("e7", "e8")
    assert len(candidates) == 4
    assert {move.promotion_piece for move in candidates} == {
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }
    result = controller.make_player_move_from_notation("e7", "e8")
    assert result.success is True
    promoted = controller.get_state().board.get_piece(
        Position.from_chess_notation("e8")
    )
    assert promoted is not None
    assert promoted.type is PieceType.QUEEN


def test_player_promotion_can_choose_rook() -> None:
    controller = _promotion_ready_controller()
    result = controller.make_player_move_from_notation(
        "e7", "e8", promotion=PieceType.ROOK
    )
    assert result.success is True
    promoted = controller.get_state().board.get_piece(
        Position.from_chess_notation("e8")
    )
    assert promoted is not None
    assert promoted.type is PieceType.ROOK


def test_state_after_plies_rebuilds_history_position() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    controller.make_player_move_from_notation("e2", "e4")
    controller.make_ai_move()
    mid = controller.state_after_plies(1)
    assert mid.ply_count == 1
    assert mid.board.get_piece(Position.from_chess_notation("e4")) is not None
    assert mid.board.get_piece(Position.from_chess_notation("e2")) is None
    live = controller.get_state()
    assert controller.state_after_plies(2).ply_count == live.ply_count
    assert controller.state_after_plies(0).ply_count == 0
