"""Apply a move by Copy-on-Move, leaving the parent state unchanged."""

from __future__ import annotations

from chessmind_ab.domain.castling_rights import CastlingRights
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.repetition import repetition_key


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
        elif move.move_type is MoveType.EN_PASSANT:
            if destination_piece is not None:
                raise IllegalStateTransitionError("En passant target must be empty")
            if move.captured_piece is None:
                raise IllegalStateTransitionError("En passant requires captured_piece")
        elif move.move_type in {
            MoveType.CASTLING_KING_SIDE,
            MoveType.CASTLING_QUEEN_SIDE,
        }:
            if destination_piece is not None:
                raise IllegalStateTransitionError("Castling destination occupied")
        elif destination_piece is not None:
            raise IllegalStateTransitionError(
                "Destination occupied for non-capture move"
            )

        child = state.copy()
        child.board.remove_piece(move.from_position)

        if move.move_type is MoveType.EN_PASSANT:
            capture_square = Position(
                row=move.from_position.row, column=move.to_position.column
            )
            removed = child.board.remove_piece(capture_square)
            if removed != move.captured_piece:
                raise IllegalStateTransitionError("En passant capture mismatch")

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

        if move.move_type is MoveType.CASTLING_KING_SIDE:
            rook_from = Position(row=move.from_position.row, column=7)
            rook_to = Position(row=move.from_position.row, column=5)
            rook = child.board.remove_piece(rook_from)
            if rook is None or rook.type is not PieceType.ROOK:
                raise IllegalStateTransitionError("Missing kingside rook")
            child.board.set_piece(rook_to, rook)
        elif move.move_type is MoveType.CASTLING_QUEEN_SIDE:
            rook_from = Position(row=move.from_position.row, column=0)
            rook_to = Position(row=move.from_position.row, column=3)
            rook = child.board.remove_piece(rook_from)
            if rook is None or rook.type is not PieceType.ROOK:
                raise IllegalStateTransitionError("Missing queenside rook")
            child.board.set_piece(rook_to, rook)

        child.castling_rights = StateTransition._updated_castling_rights(state, move)
        child.en_passant_target = StateTransition._updated_en_passant(move)
        child.halfmove_clock = StateTransition._updated_halfmove(state, move)
        child.side_to_move = state.side_to_move.opposite()
        child.ply_count = state.ply_count + 1

        key = repetition_key(child)
        irreversible = (
            move.moving_piece.type is PieceType.PAWN
            or move.captured_piece is not None
            or move.move_type
            in {MoveType.CASTLING_KING_SIDE, MoveType.CASTLING_QUEEN_SIDE}
        )
        if irreversible:
            child.repetition_keys = (key,)
        else:
            child.repetition_keys = state.repetition_keys + (key,)
        return child

    @staticmethod
    def _updated_en_passant(move: Move) -> Position | None:
        if move.move_type is not MoveType.PAWN_DOUBLE:
            return None
        mid_row = (move.from_position.row + move.to_position.row) // 2
        return Position(row=mid_row, column=move.from_position.column)

    @staticmethod
    def _updated_halfmove(state: GameState, move: Move) -> int:
        if (
            move.moving_piece.type is PieceType.PAWN
            or move.captured_piece is not None
        ):
            return 0
        return state.halfmove_clock + 1

    @staticmethod
    def _updated_castling_rights(state: GameState, move: Move) -> CastlingRights:
        rights = state.castling_rights
        color = move.moving_piece.color

        if move.moving_piece.type is PieceType.KING or move.move_type in {
            MoveType.CASTLING_KING_SIDE,
            MoveType.CASTLING_QUEEN_SIDE,
        }:
            rights = rights.without_white() if color is Color.WHITE else rights.without_black()

        if move.moving_piece.type is PieceType.ROOK:
            rights = StateTransition._revoke_rook_rights(
                rights, color, move.from_position
            )

        if move.captured_piece is not None and move.captured_piece.type is PieceType.ROOK:
            # Captured rook square: destination, or EP capture square.
            if move.move_type is MoveType.EN_PASSANT:
                square = Position(
                    row=move.from_position.row, column=move.to_position.column
                )
            else:
                square = move.to_position
            rights = StateTransition._revoke_rook_rights(
                rights, move.captured_piece.color, square
            )
        return rights

    @staticmethod
    def _revoke_rook_rights(
        rights: CastlingRights, color: Color, square: Position
    ) -> CastlingRights:
        if color is Color.WHITE and square.row == 7:
            if square.column == 7:
                return rights.without_white_king_side()
            if square.column == 0:
                return rights.without_white_queen_side()
        if color is Color.BLACK and square.row == 0:
            if square.column == 7:
                return rights.without_black_king_side()
            if square.column == 0:
                return rights.without_black_queen_side()
        return rights
