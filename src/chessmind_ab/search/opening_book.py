"""Opening book for early-game variety (play mode)."""

from __future__ import annotations

import random
from collections import deque

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition


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


def _build_book() -> dict[str, list[str]]:
    book: dict[str, list[str]] = {}
    root = create_initial_game_state()

    # Broader White first-move pool (AI as White when player is Black).
    book[position_key(root)] = [
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
    ]

    after_e4 = _apply_notation(root, "e2e4")
    book[position_key(after_e4)] = ["e7e5", "c7c5", "e7e6", "c7c6", "g8f6", "d7d5", "d7d6"]

    after_d4 = _apply_notation(root, "d2d4")
    book[position_key(after_d4)] = ["d7d5", "g8f6", "e7e6", "c7c5", "f7f5", "d7d6"]

    after_nf3 = _apply_notation(root, "g1f3")
    book[position_key(after_nf3)] = ["d7d5", "g8f6", "c7c5", "e7e6", "g7g6"]

    after_c4 = _apply_notation(root, "c2c4")
    book[position_key(after_c4)] = ["e7e5", "c7c5", "g8f6", "e7e6", "c7c6"]

    after_g3 = _apply_notation(root, "g2g3")
    book[position_key(after_g3)] = ["d7d5", "g8f6", "e7e5", "c7c5", "g7g6"]

    after_e3 = _apply_notation(root, "e2e3")
    book[position_key(after_e3)] = ["d7d5", "g8f6", "e7e5", "c7c5"]

    after_nc3 = _apply_notation(root, "b1c3")
    book[position_key(after_nc3)] = ["d7d5", "g8f6", "e7e5", "c7c5"]

    after_f4 = _apply_notation(root, "f2f4")
    book[position_key(after_f4)] = ["d7d5", "e7e5", "g8f6", "c7c5"]

    after_b3 = _apply_notation(root, "b2b3")
    book[position_key(after_b3)] = ["e7e5", "d7d5", "g8f6", "c7c5"]

    after_c3 = _apply_notation(root, "c2c3")
    book[position_key(after_c3)] = ["d7d5", "e7e5", "g8f6", "c7c5"]

    # Two-ply continuations keep games from collapsing to one line.
    e4_e5 = _apply_notation(after_e4, "e7e5")
    e4_e5_nf3 = _apply_notation(e4_e5, "g1f3")
    book[position_key(e4_e5_nf3)] = ["b8c6", "g8f6", "d7d6"]

    e4_e5_nf3_nc6 = _apply_notation(e4_e5_nf3, "b8c6")
    book[position_key(e4_e5_nf3_nc6)] = ["f1b5", "d2d4", "f1c4", "c2c3"]

    e4_c5 = _apply_notation(after_e4, "c7c5")
    e4_c5_nf3 = _apply_notation(e4_c5, "g1f3")
    book[position_key(e4_c5_nf3)] = ["d7d6", "b8c6", "e7e6", "g7g6"]

    e4_c5_nf3_d6 = _apply_notation(e4_c5_nf3, "d7d6")
    book[position_key(e4_c5_nf3_d6)] = ["d2d4", "c2c3", "b1c3"]

    e4_e6 = _apply_notation(after_e4, "e7e6")
    book[position_key(_apply_notation(e4_e6, "d2d4"))] = ["d7d5", "c7c5", "g8f6"]

    d4_d5 = _apply_notation(after_d4, "d7d5")
    book[position_key(_apply_notation(d4_d5, "c2c4"))] = ["e7e6", "c7c6", "d5c4", "g8f6"]

    d4_nf6 = _apply_notation(after_d4, "g8f6")
    book[position_key(_apply_notation(d4_nf6, "c2c4"))] = ["e7e6", "g7g6", "c7c5", "e7e5"]

    # Mirror a few replies when White is human and AI is Black after quieter starts.
    nf3_d5 = _apply_notation(after_nf3, "d7d5")
    book[position_key(_apply_notation(nf3_d5, "d2d4"))] = ["g8f6", "c7c5", "e7e6", "c8f5"]

    return book


_BOOK = _build_book()


class OpeningBook:
    """Suggest a legal book move for early positions, if any."""

    def __init__(self, max_ply: int = 12, recent_window: int = 6) -> None:
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
