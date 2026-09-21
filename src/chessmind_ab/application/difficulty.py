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
# Strength gaps stay intentional:
# - depth steps up every tier (no shared max depth between neighbors)
# - weaker tiers keep a wide root diversity window (centipawns)
# - Beginner skips the opening book so early play is not "too correct"
DIFFICULTIES: dict[str, Difficulty] = {
    "beginner": Difficulty(
        key="beginner",
        name="Beginner",
        elo=100,
        depth=1,
        diversity_window=280,
        early_diversity_window=320,
        use_opening_book=False,
        time_budget_ms=200,
        description="Depth 1, no book, often picks near-best moves. Blunders freely. ~100 chess.com.",
    ),
    "easy": Difficulty(
        key="easy",
        name="Easy",
        elo=200,
        depth=2,
        diversity_window=160,
        early_diversity_window=220,
        use_opening_book=True,
        time_budget_ms=450,
        description="Shallow look-ahead with wide move variety; still forgiving. ~200 chess.com.",
    ),
    "medium": Difficulty(
        key="medium",
        name="Medium",
        elo=300,
        depth=3,
        diversity_window=70,
        early_diversity_window=110,
        use_opening_book=True,
        time_budget_ms=1200,
        description="Casual play: deeper ID and tighter move choice. ~300 chess.com.",
    ),
    "hard": Difficulty(
        key="hard",
        name="Hard",
        elo=450,
        depth=4,
        diversity_window=25,
        early_diversity_window=45,
        use_opening_book=True,
        time_budget_ms=2500,
        description="Deeper search and longer think; fewer free gifts. ~450 chess.com.",
    ),
    "expert": Difficulty(
        key="expert",
        name="Expert",
        elo=600,
        depth=6,
        diversity_window=0,
        early_diversity_window=0,
        use_opening_book=True,
        time_budget_ms=5000,
        description="Deepest preset, always the best root move. ~600 chess.com, not FIDE club.",
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
