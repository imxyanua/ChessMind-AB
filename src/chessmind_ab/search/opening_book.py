"""Tiny opening book for early-game variety (play mode)."""

from __future__ import annotations

import random

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition

# From-to notation replies keyed by compact position fingerprint.
# Built from common first moves so AI (usually Black) does not always reply the same way.


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


def _apply_notation(state: GameState, notation: str) -> GameState:
    source = Position.from_chess_notation(notation[:2])
    target = Position.from_chess_notation(notation[2:4])
    legal = LegalMoveGenerator.generate(state)
    for move in legal:
        if move.from_position == source and move.to_position == target:
            # Prefer queen promotion if present.
            if move.promotion_piece is None or move.promotion_piece.name == "QUEEN":
                return StateTransition.apply(state, move)
    for move in legal:
        if move.from_position == source and move.to_position == target:
            return StateTransition.apply(state, move)
    raise ValueError(f"Cannot apply book move {notation}")


def _build_book() -> dict[str, list[str]]:
    book: dict[str, list[str]] = {}
    root = create_initial_game_state()

    # White first-move suggestions if AI ever plays White.
    book[position_key(root)] = ["e2e4", "d2d4", "g1f3", "c2c4"]

    # After 1.e4
    after_e4 = _apply_notation(root, "e2e4")
    book[position_key(after_e4)] = ["e7e5", "c7c5", "e7e6", "c7c6", "g8f6"]

    # After 1.d4
    after_d4 = _apply_notation(root, "d2d4")
    book[position_key(after_d4)] = ["d7d5", "g8f6", "e7e6", "c7c5"]

    # After 1.Nf3
    after_nf3 = _apply_notation(root, "g1f3")
    book[position_key(after_nf3)] = ["d7d5", "g8f6", "c7c5", "e7e6"]

    # After 1.c4
    after_c4 = _apply_notation(root, "c2c4")
    book[position_key(after_c4)] = ["e7e5", "c7c5", "g8f6", "e7e6"]

    # A couple of two-ply lines for Black after 1.e4 e5 2.Nf3
    e4_e5 = _apply_notation(after_e4, "e7e5")
    e4_e5_nf3 = _apply_notation(e4_e5, "g1f3")
    book[position_key(e4_e5_nf3)] = ["b8c6", "g8f6", "d7d6"]

    # After 1.e4 c5 2.Nf3
    e4_c5 = _apply_notation(after_e4, "c7c5")
    e4_c5_nf3 = _apply_notation(e4_c5, "g1f3")
    book[position_key(e4_c5_nf3)] = ["d7d6", "b8c6", "e7e6"]

    return book


_BOOK = _build_book()


class OpeningBook:
    """Suggest a legal book move for early positions, if any."""

    def __init__(self, max_ply: int = 8) -> None:
        self._max_ply = max_ply

    def suggest(self, state: GameState, rng: random.Random | None = None) -> Move | None:
        if state.ply_count >= self._max_ply:
            return None
        entries = _BOOK.get(position_key(state))
        if not entries:
            return None

        legal = LegalMoveGenerator.generate(state)
        by_notation = {
            f"{m.from_position.to_chess_notation()}{m.to_position.to_chess_notation()}": m
            for m in legal
            if m.promotion_piece is None
        }
        candidates = [by_notation[n] for n in entries if n in by_notation]
        if not candidates:
            return None
        chooser = rng or random.Random()
        return chooser.choice(candidates)
