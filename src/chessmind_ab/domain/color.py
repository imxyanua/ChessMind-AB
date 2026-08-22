"""Player / piece color."""

from enum import Enum, auto


class Color(Enum):
    WHITE = auto()
    BLACK = auto()

    def opposite(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE
