"""Unit tests for PseudoMoveGenerator (P2-1)."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator


def _state_with(pieces: dict[str, Piece], side: Color = Color.WHITE) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    return GameState(
        board=board,
        side_to_move=side,
        status=GameStatus.ONGOING,
        ply_count=0,
    )


def _targets(moves) -> set[str]:
    return {move.to_position.to_chess_notation() for move in moves}


def test_white_pawn_normal_and_double() -> None:
    state = _state_with({"e2": Piece(type=PieceType.PAWN, color=Color.WHITE)})
    moves = PseudoMoveGenerator.generate(state)
    assert _targets(moves) == {"e3", "e4"}
    assert any(move.move_type is MoveType.PAWN_DOUBLE for move in moves)


def test_white_pawn_blocked_cannot_double() -> None:
    state = _state_with(
        {
            "e2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "e3": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    moves = [
        m
        for m in PseudoMoveGenerator.generate(state)
        if m.from_position.to_chess_notation() == "e2"
    ]
    assert moves == []


def test_white_pawn_diagonal_capture_only() -> None:
    state = _state_with(
        {
            "e4": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "d5": Piece(type=PieceType.KNIGHT, color=Color.BLACK),
            "e5": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    moves = [
        m
        for m in PseudoMoveGenerator.generate(state)
        if m.from_position.to_chess_notation() == "e4"
    ]
    assert _targets(moves) == {"d5"}
    assert moves[0].move_type is MoveType.CAPTURE


def test_promotion_generates_four_options() -> None:
    state = _state_with({"e7": Piece(type=PieceType.PAWN, color=Color.WHITE)})
    moves = PseudoMoveGenerator.generate(state)
    assert len(moves) == 4
    assert {m.promotion_piece for m in moves} == {
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    }
    assert all(m.move_type is MoveType.PROMOTION for m in moves)


def test_knight_jumps_and_ignores_blockers() -> None:
    state = _state_with(
        {
            "e4": Piece(type=PieceType.KNIGHT, color=Color.WHITE),
            "e5": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "d6": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    moves = [
        m
        for m in PseudoMoveGenerator.generate(state)
        if m.from_position.to_chess_notation() == "e4"
    ]
    assert "d6" in _targets(moves)
    assert "f6" in _targets(moves)
    capture = next(m for m in moves if m.to_position.to_chess_notation() == "d6")
    assert capture.move_type is MoveType.CAPTURE


def test_rook_blocked_by_friendly_and_stops_after_capture() -> None:
    state = _state_with(
        {
            "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "a3": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "c1": Piece(type=PieceType.PAWN, color=Color.BLACK),
        }
    )
    moves = [
        m
        for m in PseudoMoveGenerator.generate(state)
        if m.from_position.to_chess_notation() == "a1"
    ]
    targets = _targets(moves)
    assert "a2" in targets
    assert "a3" not in targets
    assert "a4" not in targets
    assert "b1" in targets
    assert "c1" in targets
    assert "d1" not in targets


def test_bishop_rays_on_diagonals() -> None:
    state = _state_with({"c1": Piece(type=PieceType.BISHOP, color=Color.WHITE)})
    moves = PseudoMoveGenerator.generate(state)
    assert "a3" in _targets(moves)
    assert "h6" in _targets(moves)


def test_queen_combines_rook_and_bishop() -> None:
    state = _state_with({"d4": Piece(type=PieceType.QUEEN, color=Color.WHITE)})
    targets = _targets(PseudoMoveGenerator.generate(state))
    assert "d8" in targets
    assert "a4" in targets
    assert "h8" in targets
    assert "a1" in targets


def test_king_one_step_only() -> None:
    state = _state_with({"e4": Piece(type=PieceType.KING, color=Color.WHITE)})
    targets = _targets(PseudoMoveGenerator.generate(state))
    assert targets == {"d3", "d4", "d5", "e3", "e5", "f3", "f4", "f5"}


def test_generate_only_requested_color() -> None:
    state = _state_with(
        {
            "e2": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "e7": Piece(type=PieceType.PAWN, color=Color.BLACK),
        },
        side=Color.WHITE,
    )
    black_moves = PseudoMoveGenerator.generate(state, Color.BLACK)
    assert all(m.moving_piece.color is Color.BLACK for m in black_moves)
