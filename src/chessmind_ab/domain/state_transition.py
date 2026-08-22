"""Apply a move by Copy-on-Move, leaving the parent state unchanged."""

from __future__ import annotations

from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType


class IllegalStateTransitionError(ValueError):
    """Raised when apply cannot execute the given move on the state."""


class StateTransition:
    @staticmethod
    def apply(state: GameState, move: Move) -> GameState:
        source_piece = state.board.get_piece(move.from_position)
        if source_piece is None:
            raise IllegalStateTransitionError("No piece at from_position")
        if source_piece != move.moving_piece:
            raise IllegalStateTransitionError(
                "moving_piece does not match piece at from_position"
            )

        destination_piece = state.board.get_piece(move.to_position)
        if move.move_type in {MoveType.CAPTURE, MoveType.PROMOTION_CAPTURE}:
            if destination_piece is None:
                raise IllegalStateTransitionError("Capture target is empty")
            if move.captured_piece != destination_piece:
                raise IllegalStateTransitionError(
                    "captured_piece does not match piece at to_position"
                )
        elif destination_piece is not None:
            raise IllegalStateTransitionError(
                "Destination occupied for non-capture move"
            )

        child = state.copy()
        child.board.remove_piece(move.from_position)

        placed_type: PieceType
        if move.move_type in {MoveType.PROMOTION, MoveType.PROMOTION_CAPTURE}:
            if move.promotion_piece is None:
                raise IllegalStateTransitionError("Missing promotion_piece")
            placed_type = move.promotion_piece
        else:
            placed_type = move.moving_piece.type

        child.board.set_piece(
            move.to_position,
            Piece(type=placed_type, color=move.moving_piece.color),
        )
        child.side_to_move = state.side_to_move.opposite()
        child.ply_count = state.ply_count + 1
        return child
