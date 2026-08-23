"""Fixed-size transposition table for Alpha-Beta."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TTFlag(Enum):
    EXACT = auto()
    LOWER = auto()  # score is a lower bound (fail high)
    UPPER = auto()  # score is an upper bound (fail low)


@dataclass(slots=True)
class TTEntry:
    key: int
    depth: int
    score: int
    flag: TTFlag


class TranspositionTable:
    def __init__(self, size_power: int = 20) -> None:
        if size_power < 8:
            raise ValueError("size_power must be >= 8")
        self._mask = (1 << size_power) - 1
        self._entries: list[TTEntry | None] = [None] * (self._mask + 1)
        self.hits = 0
        self.stores = 0

    def clear(self) -> None:
        self._entries = [None] * (self._mask + 1)
        self.hits = 0
        self.stores = 0

    def _index(self, key: int) -> int:
        return key & self._mask

    def store(self, key: int, depth: int, score: int, flag: TTFlag) -> None:
        slot = self._index(key)
        current = self._entries[slot]
        # Prefer deeper entries when colliding.
        if current is not None and current.key == key and current.depth > depth:
            return
        self._entries[slot] = TTEntry(key=key, depth=depth, score=score, flag=flag)
        self.stores += 1

    def lookup(
        self,
        key: int,
        depth: int,
        alpha: float,
        beta: float,
    ) -> int | None:
        entry = self._entries[self._index(key)]
        if entry is None or entry.key != key or entry.depth < depth:
            return None
        self.hits += 1
        if entry.flag is TTFlag.EXACT:
            return entry.score
        if entry.flag is TTFlag.LOWER and entry.score >= beta:
            return entry.score
        if entry.flag is TTFlag.UPPER and entry.score <= alpha:
            return entry.score
        return None
