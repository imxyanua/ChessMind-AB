"""Unit tests for LegalMoveGenerator (P2-3)."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.domain.attack_detector import AttackDetector


def _state(pieces: dict[str, Piece], side: Color = Color.WHITE) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=side,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_legal_moves_are_subset_of_pseudo_moves() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a2": Piece(type=PieceType.PAWN, color=Color.WHITE),
        }
    )
    pseudo = PseudoMoveGenerator.generate(state)
    legal = LegalMoveGenerator.generate(state)
    pseudo_keys = {
        (
            m.from_position.to_chess_notation(),
            m.to_position.to_chess_notation(),
            m.move_type,
            m.promotion_piece,
        )
        for m in pseudo
    }
    for move in legal:
        key = (
            move.from_position.to_chess_notation(),
            move.to_position.to_chess_notation(),
            move.move_type,
            move.promotion_piece,
        )
        assert key in pseudo_keys


def test_pinned_piece_cannot_leave_pin_line() -> None:
    # Black rook on e8 pins white rook on e2 to white king on e1.
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e2": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "e8": Piece(type=PieceType.ROOK, color=Color.BLACK),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    legal = LegalMoveGenerator.generate(state)
    rook_moves = [
        m
        for m in legal
        if m.from_position.to_chess_notation() == "e2"
    ]
    assert all(m.to_position.column == 4 for m in rook_moves)
    assert not any(m.to_position.to_chess_notation() == "a2" for m in rook_moves)


def test_in_check_only_escaping_moves_remain() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "h4": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "e8": Piece(type=PieceType.ROOK, color=Color.BLACK),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    assert AttackDetector.is_king_in_check(state, Color.WHITE)
    legal = LegalMoveGenerator.generate(state)
    assert legal
    for move in legal:
        child = StateTransition.apply(state, move)
        assert not AttackDetector.is_king_in_check(child, Color.WHITE)


def test_after_every_legal_move_own_king_is_safe() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a7": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    side = state.side_to_move
    for move in LegalMoveGenerator.generate(state):
        child = StateTransition.apply(state, move)
        assert not AttackDetector.is_king_in_check(child, side)
