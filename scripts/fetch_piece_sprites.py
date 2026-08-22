"""Fetch Wikipedia chess piece sprites used by the GUI."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "chessmind_ab" / "assets" / "pieces"
BASE = (
    "https://raw.githubusercontent.com/oakmac/chessboardjs/master/"
    "website/img/chesspieces/wikipedia"
)

MAPPING = {
    "wP": "white_pawn",
    "wN": "white_knight",
    "wB": "white_bishop",
    "wR": "white_rook",
    "wQ": "white_queen",
    "wK": "white_king",
    "bP": "black_pawn",
    "bN": "black_knight",
    "bB": "black_bishop",
    "bR": "black_rook",
    "bQ": "black_queen",
    "bK": "black_king",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for remote_name, local_name in MAPPING.items():
        src = f"{BASE}/{remote_name}.png"
        dest = OUT / f"{local_name}.png"
        urlretrieve(src, dest)
        image = Image.open(dest).convert("RGBA").resize((128, 128), Image.Resampling.LANCZOS)
        image.save(dest)
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
