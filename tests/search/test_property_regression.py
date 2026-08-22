"""Property-style / regression tests (THIETKEDUAN §85)."""

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.board import Board
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.benchmark import benchmark_positions
from chessmind_ab.search.minimax import MinimaxSearch
from chessmind_ab.search.move_ordering import MoveOrdering


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


def _move_key(move) -> tuple:
    return (
        move.from_position.to_chess_notation(),
        move.to_position.to_chess_notation(),
        move.move_type,
        move.promotion_piece,
        move.moving_piece.type,
        move.moving_piece.color,
    )


def _sample_states() -> list[GameState]:
    return [
        create_initial_game_state(),
        _state(
            {
                "e1": Piece(type=PieceType.KING, color=Color.WHITE),
                "e8": Piece(type=PieceType.KING, color=Color.BLACK),
                "d1": Piece(type=PieceType.QUEEN, color=Color.WHITE),
                "d8": Piece(type=PieceType.QUEEN, color=Color.BLACK),
            }
        ),
        _state(
            {
                "e1": Piece(type=PieceType.KING, color=Color.WHITE),
                "e2": Piece(type=PieceType.ROOK, color=Color.WHITE),
                "e8": Piece(type=PieceType.ROOK, color=Color.BLACK),
                "a8": Piece(type=PieceType.KING, color=Color.BLACK),
            }
        ),
        benchmark_positions()["T4-endgame"],
        benchmark_positions()["T5-mate"],
    ]


def test_property_legal_moves_subset_of_pseudo_across_samples() -> None:
    for state in _sample_states():
        pseudo = {_move_key(move) for move in PseudoMoveGenerator.generate(state)}
        for move in LegalMoveGenerator.generate(state):
            assert _move_key(move) in pseudo


def test_property_own_king_safe_after_every_legal_move() -> None:
    for state in _sample_states():
        side = state.side_to_move
        for move in LegalMoveGenerator.generate(state):
            child = StateTransition.apply(state, move)
            assert not AttackDetector.is_king_in_check(child, side)


def test_property_state_transition_does_not_mutate_parent() -> None:
    state = create_initial_game_state()
    before_side = state.side_to_move
    before_ply = state.ply_count
    e2 = state.board.get_piece(Position.from_chess_notation("e2"))
    moves = LegalMoveGenerator.generate(state)
    assert moves
    child = StateTransition.apply(state, moves[0])
    assert state.side_to_move is before_side
    assert state.ply_count == before_ply
    assert state.board.get_piece(Position.from_chess_notation("e2")) == e2
    assert child is not state
    assert child.ply_count == before_ply + 1


def test_property_alpha_beta_matches_minimax_with_and_without_ordering() -> None:
    # Depth 1 keeps the suite fast while covering opening + tactical fixtures.
    for state in _sample_states():
        mini = MinimaxSearch().find_best_move(state, 1)
        plain = AlphaBetaSearch().find_best_move(state, 1)
        ordered = AlphaBetaSearch(move_ordering=MoveOrdering()).find_best_move(state, 1)
        assert plain.best_score == mini.best_score
        assert ordered.best_score == mini.best_score


def test_property_move_ordering_preserves_move_set() -> None:
    for state in _sample_states():
        original = LegalMoveGenerator.generate(state)
        ordered = MoveOrdering().order(state, list(original))
        assert {_move_key(move) for move in ordered} == {
            _move_key(move) for move in original
        }
        assert len(ordered) == len(original)


def test_double_check_forces_king_move_only() -> None:
    # White king on e1 checked by black rook on e8 and bishop on a5.
    state = _state(
        {
            "e1": Piece(type=PieceType.KING, color=Color.WHITE),
            "d2": Piece(type=PieceType.QUEEN, color=Color.WHITE),
            "e8": Piece(type=PieceType.ROOK, color=Color.BLACK),
            "a5": Piece(type=PieceType.BISHOP, color=Color.BLACK),
            "h8": Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )
    assert AttackDetector.is_king_in_check(state, Color.WHITE)
    legal = LegalMoveGenerator.generate(state)
    assert legal
    assert all(move.moving_piece.type is PieceType.KING for move in legal)
    for move in legal:
        child = StateTransition.apply(state, move)
        assert not AttackDetector.is_king_in_check(child, Color.WHITE)
