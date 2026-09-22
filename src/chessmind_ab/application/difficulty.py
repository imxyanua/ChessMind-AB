"""Play difficulty presets with chess.com-calibrated Elo labels."""

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


# Elo numbers are an approximate chess.com (new-player / bot) scale, not FIDE.
# Calibrated so Medium plays around chess.com ~300. Python search + simple eval
# is much weaker than the old 600-1400 labels suggested.
#
# Strength gaps are from move choice (depth cap + diversity + book), not wait
# time. ID aborts when the budget expires so Hard/Expert do not sit idle.
# - depth steps up every tier (no shared max depth between neighbors)
# - weaker tiers keep a wide root diversity window (centipawns)
# - Beginner skips the opening book so early play is not "too correct"
DIFFICULTIES: dict[str, Difficulty] = {
    "beginner": Difficulty(
        key="beginner",
        name="Beginner",
        elo=100,
        depth=1,
        diversity_window=350,
        early_diversity_window=420,
        use_opening_book=False,
        time_budget_ms=200,
        description="Depth 1, no book, often not the best move. Blunders freely. ~100 chess.com.",
    ),
    "easy": Difficulty(
        key="easy",
        name="Easy",
        elo=200,
        depth=2,
        diversity_window=200,
        early_diversity_window=280,
        use_opening_book=True,
        time_budget_ms=400,
        description="Shallow look-ahead with wide move variety; still forgiving. ~200 chess.com.",
    ),
    "medium": Difficulty(
        key="medium",
        name="Medium",
        elo=300,
        depth=3,
        diversity_window=80,
        early_diversity_window=130,
        use_opening_book=True,
        time_budget_ms=700,
        description="Casual play: tighter move choice, short think. ~300 chess.com.",
    ),
    "hard": Difficulty(
        key="hard",
        name="Hard",
        elo=450,
        depth=4,
        diversity_window=20,
        early_diversity_window=35,
        use_opening_book=True,
        time_budget_ms=1000,
        description="Deeper cap and fewer free gifts; search stops at the budget. ~450 chess.com.",
    ),
    "expert": Difficulty(
        key="expert",
        name="Expert",
        elo=600,
        depth=6,
        diversity_window=0,
        early_diversity_window=0,
        use_opening_book=True,
        time_budget_ms=1400,
        description="Always the best completed root move. Stops at 1.4s, not a long delay. ~600 chess.com.",
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
