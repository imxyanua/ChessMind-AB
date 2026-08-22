"""Difficulty / Elo preset tests."""

from chessmind_ab.application.difficulty import (
    DIFFICULTIES,
    difficulty_from_label,
    get_difficulty,
)
from chessmind_ab.application.game_controller import GameController


def test_five_elo_presets_exist() -> None:
    assert set(DIFFICULTIES) == {"beginner", "easy", "medium", "hard", "expert"}
    assert get_difficulty("beginner").elo == 600
    assert get_difficulty("expert").elo == 1400
    assert get_difficulty("beginner").depth < get_difficulty("expert").depth


def test_controller_applies_difficulty() -> None:
    controller = GameController(difficulty_key="beginner")
    assert controller.get_difficulty().key == "beginner"
    assert controller._ai_depth == 1
    controller.set_difficulty("hard")
    assert controller.get_difficulty().elo == 1200
    assert controller._ai_depth == 3


def test_label_roundtrip() -> None:
    hard = get_difficulty("hard")
    assert difficulty_from_label(hard.label).key == "hard"
