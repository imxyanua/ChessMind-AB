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


def test_strength_gaps_are_monotonic() -> None:
    order = ["beginner", "easy", "medium", "hard", "expert"]
    depths = [get_difficulty(key).depth for key in order]
    times = [get_difficulty(key).time_budget_ms for key in order]
    diversities = [get_difficulty(key).diversity_window for key in order]
    assert depths == sorted(depths)
    assert depths == sorted(set(depths))  # strictly increasing, no shared depth
    assert times == sorted(times)
    assert diversities == sorted(diversities, reverse=True)
    assert get_difficulty("beginner").use_opening_book is False
    assert get_difficulty("easy").use_opening_book is True
    assert get_difficulty("expert").use_opening_book is True
    assert get_difficulty("expert").diversity_window == 0
    assert get_difficulty("expert").early_diversity_window == 0


def test_controller_applies_difficulty() -> None:
    controller = GameController(difficulty_key="beginner")
    assert controller.get_difficulty().key == "beginner"
    assert controller._ai_depth == get_difficulty("beginner").depth
    assert controller.get_difficulty().time_budget_ms is not None
    controller.set_difficulty("hard")
    assert controller.get_difficulty().elo == 1200
    assert controller._ai_depth == get_difficulty("hard").depth


def test_play_presets_have_time_budgets_for_id() -> None:
    for key, diff in DIFFICULTIES.items():
        assert diff.time_budget_ms is not None, key
        assert diff.time_budget_ms > 0, key
        assert diff.depth >= 1, key


def test_label_roundtrip() -> None:
    hard = get_difficulty("hard")
    assert difficulty_from_label(hard.label).key == "hard"
