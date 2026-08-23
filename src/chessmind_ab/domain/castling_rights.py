"""Castling availability flags for both sides."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CastlingRights:
    white_king_side: bool = True
    white_queen_side: bool = True
    black_king_side: bool = True
    black_queen_side: bool = True

    def key(self) -> str:
        return (
            ("K" if self.white_king_side else "")
            + ("Q" if self.white_queen_side else "")
            + ("k" if self.black_king_side else "")
            + ("q" if self.black_queen_side else "")
            or "-"
        )

    def without_white(self) -> CastlingRights:
        return CastlingRights(
            white_king_side=False,
            white_queen_side=False,
            black_king_side=self.black_king_side,
            black_queen_side=self.black_queen_side,
        )

    def without_black(self) -> CastlingRights:
        return CastlingRights(
            white_king_side=self.white_king_side,
            white_queen_side=self.white_queen_side,
            black_king_side=False,
            black_queen_side=False,
        )

    def without_white_king_side(self) -> CastlingRights:
        return CastlingRights(
            white_king_side=False,
            white_queen_side=self.white_queen_side,
            black_king_side=self.black_king_side,
            black_queen_side=self.black_queen_side,
        )

    def without_white_queen_side(self) -> CastlingRights:
        return CastlingRights(
            white_king_side=self.white_king_side,
            white_queen_side=False,
            black_king_side=self.black_king_side,
            black_queen_side=self.black_queen_side,
        )

    def without_black_king_side(self) -> CastlingRights:
        return CastlingRights(
            white_king_side=self.white_king_side,
            white_queen_side=self.white_queen_side,
            black_king_side=False,
            black_queen_side=self.black_queen_side,
        )

    def without_black_queen_side(self) -> CastlingRights:
        return CastlingRights(
            white_king_side=self.white_king_side,
            white_queen_side=self.white_queen_side,
            black_king_side=self.black_king_side,
            black_queen_side=False,
        )
