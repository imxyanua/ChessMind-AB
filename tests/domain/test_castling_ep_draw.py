"""Tests for castling, en passant, and draw rules."""

from chessmind_ab.domain.board import Board
from chessmind_ab.domain.castling_rights import CastlingRights
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.application.pgn import format_san


def _state(pieces: dict[str, Piece], **kwargs) -> GameState:
    board = Board()
    for notation, piece in pieces.items():
        board.set_piece(Position.from_chess_notation(notation), piece)
    defaults = dict(
        board=board,
        side_to_move=Color.WHITE,
        status=GameStatus.ONGOING,
        ply_count=0,
        castling_rights=CastlingRights(
            white_king_side=False,
            white_queen_side=False,
            black_king_side=False,
            black_queen_side=False,
        ),
        en_passant_target=None,
        halfmove_clock=0,
        repetition_keys=(),
    )
    defaults.update(kwargs)
    return GameState(**defaults)


def test_white_kingside_castling_moves_rook() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "h1": Piece(type=PieceType.ROOK, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        },
        castling_rights=CastlingRights(
            white_king_side=True,
            white_queen_side=False,
            black_king_side=False,
            black_queen_side=False,
        ),
    )
    castles = [
        move
        for move in LegalMoveGenerator.generate(state)
        if move.move_type is MoveType.CASTLING_KING_SIDE
    ]
    assert len(castles) == 1
    child = StateTransition.apply(state, castles[0])
    assert child.board.get_piece(Position.from_chess_notation("g1")).type is PieceType.KING
    assert child.board.get_piece(Position.from_chess_notation("f1")).type is PieceType.ROOK
    assert format_san(state, castles[0]).startswith("O-O")


def test_en_passant_capture_removes_pawn() -> None:
    state = _state(
        {
            "e5": Piece(type=PieceType.PAWN, color=Color.WHITE),
            "d5": Piece(type=PieceType.PAWN, color=Color.BLACK),
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        },
        en_passant_target=Position.from_chess_notation("d6"),
    )
    ep_moves = [
        move
        for move in LegalMoveGenerator.generate(state)
        if move.move_type is MoveType.EN_PASSANT
    ]
    assert len(ep_moves) == 1
    child = StateTransition.apply(state, ep_moves[0])
    assert child.board.get_piece(Position.from_chess_notation("d6")).type is PieceType.PAWN
    assert child.board.get_piece(Position.from_chess_notation("d5")) is None


def test_pawn_double_sets_en_passant_target() -> None:
    state = create_initial_game_state()
    double = next(
        move
        for move in LegalMoveGenerator.generate(state)
        if move.move_type is MoveType.PAWN_DOUBLE
        and move.from_position.to_chess_notation() == "e2"
    )
    child = StateTransition.apply(state, double)
    assert child.en_passant_target == Position.from_chess_notation("e3")


def test_fifty_move_rule_draw() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
            "a1": Piece(type=PieceType.ROOK, color=Color.WHITE),
        },
        halfmove_clock=100,
    )
    assert GameStatusEvaluator.evaluate(state) is GameStatus.DRAW


def test_insufficient_material_draw() -> None:
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "e8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    assert GameStatusEvaluator.evaluate(state) is GameStatus.DRAW
