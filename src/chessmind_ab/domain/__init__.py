"""Chess domain package."""

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.board import Board, KingNotFoundError
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState, InvalidGameStateError
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.move import InvalidMoveError, Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import InvalidPositionError, Position
from chessmind_ab.domain.pseudo_move_generator import PseudoMoveGenerator
from chessmind_ab.domain.state_transition import (
    IllegalStateTransitionError,
    StateTransition,
)

__all__ = [
    "AttackDetector",
    "Board",
    "Color",
    "GameState",
    "GameStatus",
    "IllegalStateTransitionError",
    "InvalidGameStateError",
    "InvalidMoveError",
    "InvalidPositionError",
    "KingNotFoundError",
    "Move",
    "MoveType",
    "Piece",
    "PieceType",
    "Position",
    "PseudoMoveGenerator",
    "StateTransition",
]
