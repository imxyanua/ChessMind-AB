"""Unit tests for GameController."""

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_status import GameStatus


def test_start_new_game_has_initial_setup() -> None:
    controller = GameController()
    state = controller.start_new_game()
    assert state.side_to_move is Color.WHITE
    assert state.status is GameStatus.ONGOING
    assert state.ply_count == 0
    assert len(controller.get_legal_moves()) > 0


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
