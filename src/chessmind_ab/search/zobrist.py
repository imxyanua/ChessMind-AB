"""Zobrist hashing for GameState (board + side + castling + EP)."""

from __future__ import annotations

import random

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.game_state import GameState
from chessmind_ab.domain.piece_type import PieceType
from chessmind_ab.domain.position import Position

_PIECE_INDEX = {
    (Color.WHITE, PieceType.PAWN): 0,
    (Color.WHITE, PieceType.KNIGHT): 1,
    (Color.WHITE, PieceType.BISHOP): 2,
    (Color.WHITE, PieceType.ROOK): 3,
    (Color.WHITE, PieceType.QUEEN): 4,
    (Color.WHITE, PieceType.KING): 5,
    (Color.BLACK, PieceType.PAWN): 6,
    (Color.BLACK, PieceType.KNIGHT): 7,
    (Color.BLACK, PieceType.BISHOP): 8,
    (Color.BLACK, PieceType.ROOK): 9,
    (Color.BLACK, PieceType.QUEEN): 10,
    (Color.BLACK, PieceType.KING): 11,
}


def _build_tables(seed: int = 0xC0FFEE) -> tuple[list[list[int]], int, list[int], list[int]]:
    rng = random.Random(seed)
    piece_square = [[rng.getrandbits(64) for _ in range(64)] for _ in range(12)]
    side_to_move = rng.getrandbits(64)
    castling = [rng.getrandbits(64) for _ in range(4)]
    en_passant_file = [rng.getrandbits(64) for _ in range(8)]
    return piece_square, side_to_move, castling, en_passant_file


_PIECE_SQUARE, _SIDE_TO_MOVE, _CASTLING, _EN_PASSANT_FILE = _build_tables()


def zobrist_hash(state: GameState) -> int:
    value = 0
    board = state.board
    for row in range(8):
        for column in range(8):
            piece = board.get_piece(Position(row=row, column=column))
            if piece is None:
                continue
            index = _PIECE_INDEX[(piece.color, piece.type)]
            square = row * 8 + column
            value ^= _PIECE_SQUARE[index][square]
    if state.side_to_move is Color.BLACK:
        value ^= _SIDE_TO_MOVE
    rights = state.castling_rights
    if rights.white_king_side:
        value ^= _CASTLING[0]
    if rights.white_queen_side:
        value ^= _CASTLING[1]
    if rights.black_king_side:
        value ^= _CASTLING[2]
    if rights.black_queen_side:
        value ^= _CASTLING[3]
    if state.en_passant_target is not None:
        value ^= _EN_PASSANT_FILE[state.en_passant_target.column]
    return value
