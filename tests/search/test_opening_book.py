"""Opening book variety tests."""

import random

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.position import Position
from chessmind_ab.search.opening_book import OpeningBook, position_key


def _apply(state, notation: str):
    source = Position.from_chess_notation(notation[:2])
    target = Position.from_chess_notation(notation[2:4])
    for move in LegalMoveGenerator.generate(state):
        if move.from_position == source and move.to_position == target:
            return StateTransition.apply(state, move)
    raise AssertionError(notation)


def test_book_suggests_reply_after_e4() -> None:
    state = _apply(create_initial_game_state(), "e2e4")
    book = OpeningBook()
    move = book.suggest(state, random.Random(0))
    assert move is not None
    assert (
        f"{move.from_position.to_chess_notation()}{move.to_position.to_chess_notation()}"
        in {"e7e5", "c7c5", "e7e6", "c7c6", "g8f6"}
    )


def test_book_replies_vary_with_seed() -> None:
    state = _apply(create_initial_game_state(), "e2e4")
    book = OpeningBook()
    replies = set()
    for seed in range(30):
        move = book.suggest(state, random.Random(seed))
        assert move is not None
        replies.add(
            move.from_position.to_chess_notation()
            + move.to_position.to_chess_notation()
        )
    assert len(replies) >= 2


def test_controller_uses_book_on_first_ai_reply() -> None:
    controller = GameController(ai_depth=1)
    controller.start_new_game()
    controller.make_player_move_from_notation("e2", "e4")
    result = controller.make_ai_move()
    assert result.success is True
    assert result.message == "AI book move"
    assert len(controller.get_move_history()) == 2


def test_position_key_stable_for_same_state() -> None:
    state = create_initial_game_state()
    assert position_key(state) == position_key(state)
