"""Orchestrates player and AI turns without owning chess/search rules."""

from __future__ import annotations

import random
from dataclasses import dataclass

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.initial_position import create_initial_game_state
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.piece import Piece
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position
from chessmind_ab.domain.state_transition import StateTransition
from chessmind_ab.application.difficulty import (
    DEFAULT_DIFFICULTY_KEY,
    Difficulty,
    get_difficulty,
)
from chessmind_ab.application.pgn import build_pgn, format_san
from chessmind_ab.search.alpha_beta import AlphaBetaSearch
from chessmind_ab.search.iterative_deepening import iterative_deepening_search
from chessmind_ab.search.move_ordering import MoveOrdering
from chessmind_ab.search.opening_book import OpeningBook
from chessmind_ab.search.protocol import SearchAlgorithm
from chessmind_ab.search.search_result import SearchResult
from chessmind_ab.search.search_statistics import SearchStatistics
from chessmind_ab.search.transposition_table import TranspositionTable

_EARLY_PLY_LIMIT = 10


@dataclass(frozen=True, slots=True)
class MoveResult:
    success: bool
    message: str
    state: GameState


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    notation: str
    move: Move
    by_player: bool


@dataclass(slots=True)
class _Snapshot:
    state: GameState
    last_search: SearchResult | None
    history: list[HistoryEntry]
    captured_white: list[Piece]  # pieces captured BY white (black pieces)
    captured_black: list[Piece]


class GameController:
    def __init__(
        self,
        search: SearchAlgorithm | None = None,
        ai_depth: int | None = None,
        player_color: Color = Color.WHITE,
        difficulty_key: str = DEFAULT_DIFFICULTY_KEY,
    ) -> None:
        self._rng = random.Random()
        self._difficulty = get_difficulty(difficulty_key)
        depth = ai_depth if ai_depth is not None else self._difficulty.depth
        self._search = search or AlphaBetaSearch(
            move_ordering=MoveOrdering(),
            diversity_window=self._difficulty.diversity_window,
            rng=self._rng,
            transposition_table=TranspositionTable(size_power=18),
        )
        self._opening_book = OpeningBook(max_ply=8)
        self._ai_depth = depth
        self._player_color = player_color
        self._state = create_initial_game_state()
        self._last_search_result: SearchResult | None = None
        self._history: list[HistoryEntry] = []
        self._captured_by_white: list[Piece] = []
        self._captured_by_black: list[Piece] = []
        self._undo_stack: list[_Snapshot] = []

    def start_new_game(self) -> GameState:
        self._state = create_initial_game_state()
        self._last_search_result = None
        self._history.clear()
        self._captured_by_white.clear()
        self._captured_by_black.clear()
        self._undo_stack.clear()
        return self._state

    def get_state(self) -> GameState:
        return self._state

    def get_legal_moves(self) -> list[Move]:
        if self._state.status is not GameStatus.ONGOING:
            return []
        return LegalMoveGenerator.generate(self._state)

    def get_last_search_result(self) -> SearchResult | None:
        return self._last_search_result

    def get_move_history(self) -> list[HistoryEntry]:
        return list(self._history)

    def get_captured_pieces(self, by_color: Color) -> list[Piece]:
        if by_color is Color.WHITE:
            return list(self._captured_by_white)
        return list(self._captured_by_black)

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def to_pgn(
        self,
        *,
        white: str = "Player",
        black: str = "ChessMind-AB",
    ) -> str:
        return build_pgn(
            [entry.notation for entry in self._history],
            self._state.status,
            white=white,
            black=black,
        )

    def set_ai_depth(self, depth: int) -> None:
        if depth < 1:
            raise ValueError("depth must be >= 1")
        self._ai_depth = depth

    def get_difficulty(self) -> Difficulty:
        return self._difficulty

    def set_difficulty(self, difficulty_key: str) -> None:
        self._difficulty = get_difficulty(difficulty_key)
        self._ai_depth = self._difficulty.depth
        if isinstance(self._search, AlphaBetaSearch):
            self._search._diversity_window = self._difficulty.diversity_window

    def _push_undo_snapshot(self) -> None:
        self._undo_stack.append(
            _Snapshot(
                state=self._state.copy(),
                last_search=self._last_search_result,
                history=list(self._history),
                captured_white=list(self._captured_by_white),
                captured_black=list(self._captured_by_black),
            )
        )

    def undo(self) -> MoveResult:
        if not self._undo_stack:
            return MoveResult(False, "Nothing to undo", self._state)
        snap = self._undo_stack.pop()
        self._state = snap.state
        self._last_search_result = snap.last_search
        self._history = snap.history
        self._captured_by_white = snap.captured_white
        self._captured_by_black = snap.captured_black
        return MoveResult(True, "Undone", self._state)

    def _record_move(self, state_before: GameState, move: Move, by_player: bool) -> None:
        notation = format_san(state_before, move)
        self._history.append(
            HistoryEntry(notation=notation, move=move, by_player=by_player)
        )
        if move.captured_piece is not None:
            if by_player:
                self._captured_by_white.append(move.captured_piece)
            else:
                # AI is black when player is white.
                if self._player_color is Color.WHITE:
                    self._captured_by_black.append(move.captured_piece)
                else:
                    self._captured_by_white.append(move.captured_piece)

    def make_player_move(self, move: Move) -> MoveResult:
        if self._state.status is not GameStatus.ONGOING:
            return MoveResult(False, "Game already over", self._state)
        if self._state.side_to_move is not self._player_color:
            return MoveResult(False, "Not player's turn", self._state)

        legal = LegalMoveGenerator.generate(self._state)
        if move not in legal:
            return MoveResult(False, "Illegal move", self._state)

        self._push_undo_snapshot()
        before = self._state
        self._state = StateTransition.apply(self._state, move)
        self._state.status = GameStatusEvaluator.evaluate(self._state)
        self._record_move(before, move, by_player=True)
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

        if self._difficulty.use_opening_book:
            book_move = self._opening_book.suggest(self._state, self._rng)
            if book_move is not None:
                self._last_search_result = SearchResult(
                    best_move=book_move,
                    best_score=0,
                    statistics=SearchStatistics(),
                )
                before = self._state
                self._state = StateTransition.apply(self._state, book_move)
                self._state.status = GameStatusEvaluator.evaluate(self._state)
                self._record_move(before, book_move, by_player=False)
                return MoveResult(True, "AI book move", self._state)

        diversity = (
            self._difficulty.early_diversity_window
            if self._state.ply_count < _EARLY_PLY_LIMIT
            else self._difficulty.diversity_window
        )
        if isinstance(self._search, AlphaBetaSearch):
            budget = self._difficulty.time_budget_ms
            if budget is not None and budget > 0:
                result = iterative_deepening_search(
                    self._search,
                    self._state,
                    time_budget_ms=float(budget),
                    max_depth=self._ai_depth,
                    diversity_window=diversity,
                )
            else:
                result = self._search.find_best_move(
                    self._state, self._ai_depth, diversity_window=diversity
                )
        else:
            result = self._search.find_best_move(self._state, self._ai_depth)
        self._last_search_result = result
        if result.best_move is None:
            self._state.status = GameStatusEvaluator.evaluate(self._state)
            return MoveResult(False, "No AI move", self._state)

        # Snapshot already taken on player move; AI continues from that branch.
        # For undo of a full turn (player+AI), one snapshot before player is enough.
        before = self._state
        self._state = StateTransition.apply(self._state, result.best_move)
        self._state.status = GameStatusEvaluator.evaluate(self._state)
        self._record_move(before, result.best_move, by_player=False)
        return MoveResult(True, "AI moved", self._state)


def material_sort_key(piece: Piece) -> int:
    order = {
        PieceType.QUEEN: 0,
        PieceType.ROOK: 1,
        PieceType.BISHOP: 2,
        PieceType.KNIGHT: 3,
        PieceType.PAWN: 4,
        PieceType.KING: 5,
    }
    return order[piece.type]
