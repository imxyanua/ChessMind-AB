"""Generate pseudo-legal moves (movement rules only, no king safety)."""

from __future__ import annotations

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position

_PROMOTION_CHOICES = (
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT,
)

_KNIGHT_DELTAS = (
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
)

_KING_DELTAS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)

_BISHOP_DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_ROOK_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_QUEEN_DIRS = _BISHOP_DIRS + _ROOK_DIRS


def _in_bounds(row: int, column: int) -> bool:
    return 0 <= row < 8 and 0 <= column < 8


class PseudoMoveGenerator:
    @staticmethod
    def generate(state: GameState, color: Color | None = None) -> list[Move]:
        side = state.side_to_move if color is None else color
        moves: list[Move] = []
        for row in range(8):
            for column in range(8):
                position = Position(row=row, column=column)
                piece = state.board.get_piece(position)
                if piece is None or piece.color is not side:
                    continue
                moves.extend(
                    PseudoMoveGenerator._generate_for_piece(state, position, piece)
                )
        return moves

    @staticmethod
    def _generate_for_piece(
        state: GameState, position: Position, piece: Piece
    ) -> list[Move]:
        if piece.type is PieceType.PAWN:
            return PseudoMoveGenerator._pawn_moves(state, position, piece)
        if piece.type is PieceType.KNIGHT:
            return PseudoMoveGenerator._step_moves(
                state, position, piece, _KNIGHT_DELTAS
            )
        if piece.type is PieceType.KING:
            return PseudoMoveGenerator._step_moves(
                state, position, piece, _KING_DELTAS
            )
        if piece.type is PieceType.BISHOP:
            return PseudoMoveGenerator._ray_moves(
                state, position, piece, _BISHOP_DIRS
            )
        if piece.type is PieceType.ROOK:
            return PseudoMoveGenerator._ray_moves(state, position, piece, _ROOK_DIRS)
        if piece.type is PieceType.QUEEN:
            return PseudoMoveGenerator._ray_moves(
                state, position, piece, _QUEEN_DIRS
            )
        return []

    @staticmethod
    def _pawn_moves(state: GameState, position: Position, piece: Piece) -> list[Move]:
        moves: list[Move] = []
        direction = -1 if piece.color is Color.WHITE else 1
        start_row = 6 if piece.color is Color.WHITE else 1
        promotion_row = 0 if piece.color is Color.WHITE else 7

        one_row = position.row + direction
        if _in_bounds(one_row, position.column):
            one_step = Position(row=one_row, column=position.column)
            if state.board.get_piece(one_step) is None:
                moves.extend(
                    PseudoMoveGenerator._pawn_forward_or_promote(
                        position, one_step, piece, MoveType.NORMAL, promotion_row
                    )
                )
                two_row = position.row + 2 * direction
                if position.row == start_row and _in_bounds(two_row, position.column):
                    two_step = Position(row=two_row, column=position.column)
                    if state.board.get_piece(two_step) is None:
                        moves.append(
                            Move(
                                from_position=position,
                                to_position=two_step,
                                moving_piece=piece,
                                move_type=MoveType.PAWN_DOUBLE,
                            )
                        )

        for dc in (-1, 1):
            capture_row = position.row + direction
            capture_col = position.column + dc
            if not _in_bounds(capture_row, capture_col):
                continue
            target = Position(row=capture_row, column=capture_col)
            occupant = state.board.get_piece(target)
            if occupant is None or occupant.color is piece.color:
                continue
            if target.row == promotion_row:
                for promo in _PROMOTION_CHOICES:
                    moves.append(
                        Move(
                            from_position=position,
                            to_position=target,
                            moving_piece=piece,
                            move_type=MoveType.PROMOTION_CAPTURE,
                            captured_piece=occupant,
                            promotion_piece=promo,
                        )
                    )
            else:
                moves.append(
                    Move(
                        from_position=position,
                        to_position=target,
                        moving_piece=piece,
                        move_type=MoveType.CAPTURE,
                        captured_piece=occupant,
                    )
                )
        return moves

    @staticmethod
    def _pawn_forward_or_promote(
        source: Position,
        destination: Position,
        piece: Piece,
        normal_type: MoveType,
        promotion_row: int,
    ) -> list[Move]:
        if destination.row == promotion_row:
            return [
                Move(
                    from_position=source,
                    to_position=destination,
                    moving_piece=piece,
                    move_type=MoveType.PROMOTION,
                    promotion_piece=promo,
                )
                for promo in _PROMOTION_CHOICES
            ]
        return [
            Move(
                from_position=source,
                to_position=destination,
                moving_piece=piece,
                move_type=normal_type,
            )
        ]

    @staticmethod
    def _step_moves(
        state: GameState,
        position: Position,
        piece: Piece,
        deltas: tuple[tuple[int, int], ...],
    ) -> list[Move]:
        moves: list[Move] = []
        for dr, dc in deltas:
            row = position.row + dr
            column = position.column + dc
            if not _in_bounds(row, column):
                continue
            target = Position(row=row, column=column)
            occupant = state.board.get_piece(target)
            if occupant is None:
                moves.append(
                    Move(
                        from_position=position,
                        to_position=target,
                        moving_piece=piece,
                        move_type=MoveType.NORMAL,
                    )
                )
            elif occupant.color is not piece.color:
                moves.append(
                    Move(
                        from_position=position,
                        to_position=target,
                        moving_piece=piece,
                        move_type=MoveType.CAPTURE,
                        captured_piece=occupant,
                    )
                )
        return moves

    @staticmethod
    def _ray_moves(
        state: GameState,
        position: Position,
        piece: Piece,
        directions: tuple[tuple[int, int], ...],
    ) -> list[Move]:
        moves: list[Move] = []
        for dr, dc in directions:
            row = position.row + dr
            column = position.column + dc
            while _in_bounds(row, column):
                target = Position(row=row, column=column)
                occupant = state.board.get_piece(target)
                if occupant is None:
                    moves.append(
                        Move(
                            from_position=position,
                            to_position=target,
                            moving_piece=piece,
                            move_type=MoveType.NORMAL,
                        )
                    )
                else:
                    if occupant.color is not piece.color:
                        moves.append(
                            Move(
                                from_position=position,
                                to_position=target,
                                moving_piece=piece,
                                move_type=MoveType.CAPTURE,
                                captured_piece=occupant,
                            )
                        )
                    break
                row += dr
                column += dc
        return moves
