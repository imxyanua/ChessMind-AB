"""Position keys used for threefold-repetition detection."""

from __future__ import annotations

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.position import Position


def repetition_key(state: GameState) -> str:
    """Key ignores clocks; includes side, castling rights, and EP target."""
    cells: list[str] = []
    for row in range(8):
        for column in range(8):
            piece = state.board.get_piece(Position(row=row, column=column))
            if piece is None:
                cells.append(".")
            else:
                cells.append(f"{piece.color.name[0]}{piece.type.name[0]}")
    ep = (
        state.en_passant_target.to_chess_notation()
        if state.en_passant_target is not None
        else "-"
    )
    return (
        "".join(cells)
        + "|"
        + state.side_to_move.name
        + "|"
        + state.castling_rights.key()
        + "|"
        + ep
    )
