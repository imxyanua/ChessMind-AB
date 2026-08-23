"""SAN formatting and PGN export helpers."""

from __future__ import annotations

from datetime import date

from chessmind_ab.domain.attack_detector import AttackDetector
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.game_status import GameStatus
from chessmind_ab.domain.game_status_evaluator import GameStatusEvaluator
from chessmind_ab.domain.legal_move_generator import LegalMoveGenerator
from chessmind_ab.domain.move import Move
from chessmind_ab.domain.move_type import MoveType
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.state_transition import StateTransition

_PIECE_LETTER = {
    PieceType.KNIGHT: "N",
    PieceType.BISHOP: "B",
    PieceType.ROOK: "R",
    PieceType.QUEEN: "Q",
    PieceType.KING: "K",
}

_PROMO_LETTER = {
    PieceType.QUEEN: "Q",
    PieceType.ROOK: "R",
    PieceType.BISHOP: "B",
    PieceType.KNIGHT: "N",
}


def format_san(state_before: GameState, move: Move) -> str:
    """Return Standard Algebraic Notation for ``move`` played from ``state_before``."""
    if move.move_type is MoveType.CASTLING_KING_SIDE:
        san = "O-O"
    elif move.move_type is MoveType.CASTLING_QUEEN_SIDE:
        san = "O-O-O"
    else:
        san = _format_san_body(state_before, move)

    after = StateTransition.apply(state_before, move)
    after.status = GameStatusEvaluator.evaluate(after)
    if after.status in {
        GameStatus.WHITE_WINS_CHECKMATE,
        GameStatus.BLACK_WINS_CHECKMATE,
    }:
        san += "#"
    elif AttackDetector.is_king_in_check(after, after.side_to_move):
        san += "+"
    return san


def _format_san_body(state_before: GameState, move: Move) -> str:
    is_capture = move.captured_piece is not None
    piece_type = move.moving_piece.type
    to_sq = move.to_position.to_chess_notation()

    if piece_type is PieceType.PAWN:
        san = ""
        if is_capture:
            san = move.from_position.to_chess_notation()[0] + "x"
        san += to_sq
        if move.promotion_piece is not None:
            san += "=" + _PROMO_LETTER[move.promotion_piece]
    else:
        san = _PIECE_LETTER[piece_type]
        san += _disambiguation(state_before, move)
        if is_capture:
            san += "x"
        san += to_sq
    return san


def _disambiguation(state: GameState, move: Move) -> str:
    others = [
        candidate
        for candidate in LegalMoveGenerator.generate(state)
        if candidate.moving_piece.type is move.moving_piece.type
        and candidate.to_position == move.to_position
        and candidate.from_position != move.from_position
    ]
    if not others:
        return ""

    from_sq = move.from_position.to_chess_notation()
    same_file = [
        other
        for other in others
        if other.from_position.column == move.from_position.column
    ]
    if not same_file:
        return from_sq[0]

    same_rank = [
        other for other in others if other.from_position.row == move.from_position.row
    ]
    if not same_rank:
        return from_sq[1]
    return from_sq


def result_token(status: GameStatus) -> str:
    if status is GameStatus.WHITE_WINS_CHECKMATE:
        return "1-0"
    if status is GameStatus.BLACK_WINS_CHECKMATE:
        return "0-1"
    if status in {GameStatus.STALEMATE, GameStatus.DRAW}:
        return "1/2-1/2"
    return "*"


def build_pgn(
    history_sans: list[str],
    status: GameStatus,
    *,
    white: str = "Player",
    black: str = "ChessMind-AB",
    event: str = "ChessMind-AB Game",
    site: str = "Local",
    game_date: date | None = None,
) -> str:
    """Build a minimal PGN document from a list of SAN plies."""
    when = game_date or date.today()
    result = result_token(status)
    headers = [
        f'[Event "{event}"]',
        f'[Site "{site}"]',
        f'[Date "{when.strftime("%Y.%m.%d")}"]',
        '[Round "1"]',
        f'[White "{white}"]',
        f'[Black "{black}"]',
        f'[Result "{result}"]',
    ]

    moves: list[str] = []
    for index in range(0, len(history_sans), 2):
        number = index // 2 + 1
        white_san = history_sans[index]
        if index + 1 < len(history_sans):
            black_san = history_sans[index + 1]
            moves.append(f"{number}. {white_san} {black_san}")
        else:
            moves.append(f"{number}. {white_san}")

    body = " ".join(moves)
    if body:
        body = f"{body} {result}"
    else:
        body = result
    return "\n".join(headers) + "\n\n" + body + "\n"
