"""Opening book for early-game variety (play mode)."""

from __future__ import annotations

import random
from collections import defaultdict, deque

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.opening_lines import ECO_LINES


def position_key(state: GameState) -> str:
    cells: list[str] = []
    for row in range(8):
        for column in range(8):
            piece = state.board.get_piece(Position(row=row, column=column))
            if piece is None:
                continue
            cells.append(
                f"{row}{column}{piece.color.name[0]}{piece.type.name[0]}"
            )
    return f"{state.side_to_move.name}|{'/'.join(cells)}"


def move_notation(move: Move) -> str:
    return (
        f"{move.from_position.to_chess_notation()}"
        f"{move.to_position.to_chess_notation()}"
    )


def _apply_notation(state: GameState, notation: str) -> GameState:
    source = Position.from_chess_notation(notation[:2])
    target = Position.from_chess_notation(notation[2:4])
    legal = LegalMoveGenerator.generate(state)
    for move in legal:
        if move.from_position == source and move.to_position == target:
            if move.promotion_piece is None or move.promotion_piece.name == "QUEEN":
                return StateTransition.apply(state, move)
    for move in legal:
        if move.from_position == source and move.to_position == target:
            return StateTransition.apply(state, move)
    raise ValueError(f"Cannot apply book move {notation}")


def _add_move(book: dict[str, list[str]], key: str, notation: str) -> None:
    entries = book.setdefault(key, [])
    if notation not in entries:
        entries.append(notation)


def _build_book() -> dict[str, list[str]]:
    book: dict[str, list[str]] = defaultdict(list)

    # Seed a broad White first-move pool even before ECO lines expand it.
    root = create_initial_game_state()
    for notation in (
        "e2e4",
        "d2d4",
        "g1f3",
        "c2c4",
        "g2g3",
        "e2e3",
        "b1c3",
        "f2f4",
        "b2b3",
        "c2c3",
    ):
        _add_move(book, position_key(root), notation)

    for name, line in ECO_LINES:
        state = create_initial_game_state()
        try:
            for notation in line:
                key = position_key(state)
                _add_move(book, key, notation)
                state = _apply_notation(state, notation)
        except ValueError as exc:
            raise ValueError(f"Invalid ECO line {name!r}: {exc}") from exc

    return dict(book)


_BOOK = _build_book()


def book_size() -> tuple[int, int]:
    """Return (position_count, total_move_entries)."""
    return len(_BOOK), sum(len(moves) for moves in _BOOK.values())


class OpeningBook:
    """Suggest a legal book move for early positions, if any."""

    def __init__(self, max_ply: int = 16, recent_window: int = 8) -> None:
        self._max_ply = max_ply
        self._recent: deque[str] = deque(maxlen=max(1, recent_window))

    def suggest(self, state: GameState, rng: random.Random | None = None) -> Move | None:
        if state.ply_count >= self._max_ply:
            return None
        entries = _BOOK.get(position_key(state))
        if not entries:
            return None

        legal = LegalMoveGenerator.generate(state)
        by_notation = {
            move_notation(move): move
            for move in legal
            if move.promotion_piece is None
        }
        candidates = [by_notation[n] for n in entries if n in by_notation]
        if not candidates:
            return None

        chooser = rng or random.Random()
        recent = set(self._recent)
        fresh = [move for move in candidates if move_notation(move) not in recent]
        pool = fresh or candidates
        chosen = chooser.choice(pool)
        self._recent.append(move_notation(chosen))
        return chosen

    def clear_recent(self) -> None:
        self._recent.clear()
