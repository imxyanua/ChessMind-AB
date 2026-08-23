"""Play difficulty presets mapped from human-facing Elo labels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Difficulty:
    key: str
    name: str
    elo: int
    depth: int
    diversity_window: int
    early_diversity_window: int
    use_opening_book: bool
    description: str
    # Soft think-time for iterative deepening in play mode.
    # None keeps fixed-depth search (useful for tests / overrides).
    time_budget_ms: int | None = None

    @property
    def label(self) -> str:
        return f"{self.name} · ~{self.elo} Elo"


DIFFICULTIES: dict[str, Difficulty] = {
    "beginner": Difficulty(
        key="beginner",
        name="Beginner",
        elo=600,
        depth=2,
        diversity_window=120,
        early_diversity_window=160,
        use_opening_book=True,
        time_budget_ms=250,
        description="Very gentle replies; short think time with ID.",
    ),
    "easy": Difficulty(
        key="easy",
        name="Easy",
        elo=800,
        depth=3,
        diversity_window=90,
        early_diversity_window=130,
        use_opening_book=True,
        time_budget_ms=500,
        description="Looks a bit ahead; still forgiving.",
    ),
    "medium": Difficulty(
        key="medium",
        name="Medium",
        elo=1000,
        depth=3,
        diversity_window=55,
        early_diversity_window=90,
        use_opening_book=True,
        time_budget_ms=900,
        description="Solid casual play with opening variety.",
    ),
    "hard": Difficulty(
        key="hard",
        name="Hard",
        elo=1200,
        depth=4,
        diversity_window=35,
        early_diversity_window=60,
        use_opening_book=True,
        time_budget_ms=1500,
        description="Deeper ID search; fewer free blunders.",
    ),
    "expert": Difficulty(
        key="expert",
        name="Expert",
        elo=1400,
        depth=5,
        diversity_window=15,
        early_diversity_window=25,
        use_opening_book=True,
        time_budget_ms=2500,
        description="Strongest preset (ID + book variety + longer think).",
    ),
}

DEFAULT_DIFFICULTY_KEY = "medium"


def get_difficulty(key: str) -> Difficulty:
    if key not in DIFFICULTIES:
        raise KeyError(f"Unknown difficulty: {key}")
    return DIFFICULTIES[key]


def difficulty_labels() -> list[str]:
    return [diff.label for diff in DIFFICULTIES.values()]


def difficulty_from_label(label: str) -> Difficulty:
    for diff in DIFFICULTIES.values():
        if diff.label == label:
            return diff
    raise KeyError(f"Unknown difficulty label: {label}")
