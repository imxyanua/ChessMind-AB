"""Unit tests for AttackDetector (P2-2)."""

import ast
from pathlib import Path

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position


def _state(pieces: dict[str, Piece]) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def test_pawn_attacks_diagonally_not_forward() -> None:
    state = _state({"e4": Piece(type=PieceType.PAWN, color=Color.WHITE)})
    assert AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("d5"), Color.WHITE
    )
    assert AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("f5"), Color.WHITE
    )
    assert not AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("e5"), Color.WHITE
    )


def test_knight_attack() -> None:
    state = _state({"e4": Piece(type=PieceType.KNIGHT, color=Color.WHITE)})
    assert AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("d6"), Color.WHITE
    )


def test_blocked_sliding_attack() -> None:
    state = _state(
        {
            "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "a3": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    assert AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("a3"), Color.WHITE
    )
    assert not AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("a4"), Color.WHITE
    )


def test_king_adjacent_attack() -> None:
    state = _state({"e4": Piece(type=PieceType.KING, color=Color.WHITE)})
    assert AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("e5"), Color.WHITE
    )
    assert not AttackDetector.is_square_attacked(
        state, Position.from_chess_notation("e6"), Color.WHITE
    )


def test_is_king_in_check() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            "e8": Piece(type=PieceType.ROOK, color=Color.BLACK),
        }
    )
    assert AttackDetector.is_king_in_check(state, Color.WHITE)
    assert not AttackDetector.is_king_in_check(state, Color.BLACK)


def test_attack_detector_source_does_not_import_legal_move_generator() -> None:
    import chessmind_ab.domain.attack_detector as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "legal_move" not in node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "legal_move" not in alias.name
