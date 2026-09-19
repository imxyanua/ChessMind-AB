"""Evaluate terminal/non-terminal game status from legal moves."""

from __future__ import annotations

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.repetition import repetition_key


class GameStatusEvaluator:
    @staticmethod
    def evaluate(state: GameState) -> GameStatus:
        if state.halfmove_clock >= 100:
            return GameStatus.DRAW
        if GameStatusEvaluator._is_threefold(state):
            return GameStatus.DRAW
        if GameStatusEvaluator._insufficient_material(state):
            return GameStatus.DRAW

        legal_moves = LegalMoveGenerator.generate(state)
        if legal_moves:
            return GameStatus.ONGOING

        in_check = AttackDetector.is_king_in_check(state, state.side_to_move)
        if in_check:
            if state.side_to_move is Color.WHITE:
                return GameStatus.BLACK_WINS_CHECKMATE
            return GameStatus.WHITE_WINS_CHECKMATE
        return GameStatus.STALEMATE

    @staticmethod
    def _is_threefold(state: GameState) -> bool:
        key = repetition_key(state)
        return state.repetition_keys.count(key) >= 3

    @staticmethod
    def _insufficient_material(state: GameState) -> bool:
        knights = 0
        bishop_colors: list[int] = []
        for row in range(8):
            for column in range(8):
                piece = state.board.get_piece(Position(row=row, column=column))
                if piece is None or piece.type is PieceType.KING:
                    continue
                if piece.type is PieceType.KNIGHT:
                    knights += 1
                    continue
                if piece.type is PieceType.BISHOP:
                    bishop_colors.append((row + column) % 2)
                    continue
                return False
        if knights:
            return knights == 1 and not bishop_colors
        if not bishop_colors:
            return True
        return len(set(bishop_colors)) == 1
