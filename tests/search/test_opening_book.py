"""Opening book variety tests."""

import random

from chessmind_ab.application.game_controller import GameController
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.opening_book import OpeningBook, move_notation, position_key


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
    assert move_notation(move) in {
        "e7e5",
        "c7c5",
        "e7e6",
        "c7c6",
        "g8f6",
        "d7d5",
        "d7d6",
    }


def test_book_replies_vary_with_seed() -> None:
    state = _apply(create_initial_game_state(), "e2e4")
    book = OpeningBook()
    replies = set()
    for seed in range(40):
        move = book.suggest(state, random.Random(seed))
        assert move is not None
        replies.add(move_notation(move))
    assert len(replies) >= 3


def test_white_first_moves_have_broad_book_pool() -> None:
    root = create_initial_game_state()
    book = OpeningBook(recent_window=8)
    first_moves = set()
    for seed in range(80):
        move = book.suggest(root, random.Random(seed))
        assert move is not None
        first_moves.add(move_notation(move))
    assert len(first_moves) >= 5
    assert {"e2e4", "d2d4", "g1f3", "c2c4"} <= first_moves


def test_book_avoids_immediate_repeat_when_possible() -> None:
    root = create_initial_game_state()
    book = OpeningBook(recent_window=4)
    rng = random.Random(1)
    first = move_notation(book.suggest(root, rng))
    second = move_notation(book.suggest(root, rng))
    third = move_notation(book.suggest(root, rng))
    # With a wide pool, consecutive picks should usually differ.
    assert len({first, second, third}) >= 2


def test_controller_ai_as_white_opens_varied_across_new_games() -> None:
    controller = GameController(difficulty_key="medium", player_color=Color.BLACK)
    openings = set()
    for _ in range(24):
        controller.start_new_game()
        result = controller.make_ai_move()
        assert result.success is True
        assert result.message == "AI book move"
        move = controller.get_move_history()[0].move
        openings.add(move_notation(move))
    assert len(openings) >= 4


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
