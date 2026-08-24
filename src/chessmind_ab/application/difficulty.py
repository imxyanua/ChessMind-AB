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


# Strength gaps are intentional for play / AI vs AI demos:
# - depth steps up every tier (no shared max depth between neighbors)
# - weaker tiers keep a wide root diversity window (centipawns)
# - Beginner skips the opening book so early play is not "too correct"
DIFFICULTIES: dict[str, Difficulty] = {
    "beginner": Difficulty(
        key="beginner",
        name="Beginner",
        elo=600,
        depth=1,
        diversity_window=280,
        early_diversity_window=320,
        use_opening_book=False,
        time_budget_ms=200,
        description="Depth 1, no book, often picks near-best moves — blunders freely.",
    ),
    "easy": Difficulty(
        key="easy",
        name="Easy",
        elo=800,
        depth=2,
        diversity_window=160,
        early_diversity_window=220,
        use_opening_book=True,
        time_budget_ms=450,
        description="Shallow look-ahead with wide move variety; still forgiving.",
    ),
    "medium": Difficulty(
        key="medium",
        name="Medium",
        elo=1000,
        depth=3,
        diversity_window=70,
        early_diversity_window=110,
        use_opening_book=True,
        time_budget_ms=1200,
        description="Solid casual play: deeper ID and tighter move choice.",
    ),
    "hard": Difficulty(
        key="hard",
        name="Hard",
        elo=1200,
        depth=4,
        diversity_window=25,
        early_diversity_window=45,
        use_opening_book=True,
        time_budget_ms=2500,
        description="Deeper search and longer think; fewer free gifts.",
    ),
    "expert": Difficulty(
        key="expert",
        name="Expert",
        elo=1400,
        depth=6,
        diversity_window=0,
        early_diversity_window=0,
        use_opening_book=True,
        time_budget_ms=5000,
        description="Deepest preset, always takes the best root move, longest think.",
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
