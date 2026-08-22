"""Chess piece data (type + color only)."""

from __future__ import annotations

from dataclasses import dataclass

from chessmind_ab.domain.color import Color
from chessmind_ab.domain.piece_type import PieceType


@dataclass(frozen=True, slots=True)
class Piece:
    type: PieceType
    color: Color
