"""Orchestrates player and AI turns without owning chess/search rules."""

from __future__ import annotations

from dataclasses import dataclass

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.move_ordering import MoveOrdering
from chessmind_ab.search.protocol import SearchAlgorithm
from chessmind_ab.search.search_result import SearchResult


@dataclass(frozen=True, slots=True)
class MoveResult:
    success: bool
    message: str
    state: GameState


class GameController:
    def __init__(
        self,
        search: SearchAlgorithm | None = None,
        ai_depth: int = 3,
        player_color: Color = Color.WHITE,
    ) -> None:
        self._search = search or AlphaBetaSearch(move_ordering=MoveOrdering())
        self._ai_depth = ai_depth
        self._player_color = player_color
        self._state = create_initial_game_state()
        self._last_search_result: SearchResult | None = None

    def start_new_game(self) -> GameState:
        self._state = create_initial_game_state()
        self._last_search_result = None
        return self._state

    def get_state(self) -> GameState:
        return self._state

    def get_legal_moves(self) -> list[Move]:
        if self._state.status is not GameStatus.ONGOING:
            return []
        return LegalMoveGenerator.generate(self._state)

    def get_last_search_result(self) -> SearchResult | None:
        return self._last_search_result

    def set_ai_depth(self, depth: int) -> None:
        if depth < 1:
            raise ValueError("depth must be >= 1")
        self._ai_depth = depth

    def make_player_move(self, move: Move) -> MoveResult:
        if self._state.status is not GameStatus.ONGOING:
            return MoveResult(False, "Game already over", self._state)
        if self._state.side_to_move is not self._player_color:
            return MoveResult(False, "Not player's turn", self._state)

        legal = LegalMoveGenerator.generate(self._state)
        if move not in legal:
            return MoveResult(False, "Illegal move", self._state)

        self._state = StateTransition.apply(self._state, move)
        self._state.status = GameStatusEvaluator.evaluate(self._state)
        return MoveResult(True, "OK", self._state)

    def make_player_move_from_notation(self, from_sq: str, to_sq: str) -> MoveResult:
        try:
            source = Position.from_chess_notation(from_sq)
            target = Position.from_chess_notation(to_sq)
        except Exception as exc:  # noqa: BLE001 - business validation path
            return MoveResult(False, f"Invalid coordinate: {exc}", self._state)

        piece = self._state.board.get_piece(source)
        if piece is None:
            return MoveResult(False, "Empty source", self._state)
        if piece.color is not self._state.side_to_move:
            return MoveResult(False, "Wrong color", self._state)

        candidates = [
            move
            for move in self.get_legal_moves()
            if move.from_position == source and move.to_position == target
        ]
        if not candidates:
            return MoveResult(False, "Illegal move", self._state)
        # Prefer queen promotion when multiple promotion options exist.
        chosen = candidates[0]
        for move in candidates:
            if move.promotion_piece is not None and move.promotion_piece.name == "QUEEN":
                chosen = move
                break
        return self.make_player_move(chosen)

    def make_ai_move(self) -> MoveResult:
        if self._state.status is not GameStatus.ONGOING:
            return MoveResult(False, "Game already over", self._state)
        if self._state.side_to_move is self._player_color:
            return MoveResult(False, "Not AI turn", self._state)

        result = self._search.find_best_move(self._state, self._ai_depth)
        self._last_search_result = result
        if result.best_move is None:
            self._state.status = GameStatusEvaluator.evaluate(self._state)
            return MoveResult(False, "No AI move", self._state)

        self._state = StateTransition.apply(self._state, result.best_move)
        self._state.status = GameStatusEvaluator.evaluate(self._state)
        return MoveResult(True, "AI moved", self._state)
