"""Generate simple Staunton-like PNG piece sprites into package assets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "chessmind_ab" / "assets" / "pieces"
SIZE = 128


def draw_piece(kind: str, color_name: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if color_name == "white":
        fill = (245, 245, 245, 255)
        stroke = (40, 40, 40, 255)
        accent = (220, 220, 220, 255)
    else:
        fill = (35, 35, 40, 255)
        stroke = (20, 20, 20, 255)
        accent = (70, 70, 80, 255)

    def ellipse(box, col):
        draw.ellipse(box, fill=col, outline=stroke, width=3)

    def rect(box, col):
        draw.rounded_rectangle(box, radius=8, fill=col, outline=stroke, width=3)

    def poly(pts, col):
        draw.polygon(pts, fill=col, outline=stroke)

    def pedestal() -> None:
        rect((34, 96, 94, 112), fill)
        rect((28, 108, 100, 118), fill)

    if kind == "pawn":
        ellipse((44, 28, 84, 68), fill)
        poly([(40, 78), (88, 78), (78, 98), (50, 98)], fill)
        pedestal()
    elif kind == "rook":
        rect((42, 34, 86, 98), fill)
        for x in (40, 56, 72):
            rect((x, 22, x + 14, 40), fill)
        pedestal()
    elif kind == "knight":
        poly(
            [
                (86, 100),
                (40, 100),
                (46, 70),
                (38, 58),
                (48, 40),
                (62, 28),
                (78, 34),
                (84, 52),
                (72, 58),
                (88, 78),
            ],
            fill,
        )
        ellipse((66, 38, 78, 50), accent)
        pedestal()
    elif kind == "bishop":
        ellipse((50, 22, 78, 50), fill)
        poly([(64, 48), (44, 96), (84, 96)], fill)
        draw.line((64, 30, 64, 46), fill=stroke, width=3)
        pedestal()
    elif kind == "queen":
        poly(
            [(34, 78), (94, 78), (84, 42), (74, 58), (64, 30), (54, 58), (44, 42)],
            fill,
        )
        for x in (44, 54, 64, 74, 84):
            ellipse((x - 6, 24, x + 6, 36), fill)
        pedestal()
    elif kind == "king":
        rect((50, 48, 78, 98), fill)
        rect((58, 18, 70, 54), fill)
        rect((46, 28, 82, 40), fill)
        pedestal()
    else:
        raise ValueError(kind)

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((36, 108, 92, 124), fill=(0, 0, 0, 60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    out = Image.alpha_composite(shadow, img)
    if color_name == "white":
        highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        highlight_draw = ImageDraw.Draw(highlight)
        highlight_draw.ellipse((48, 30, 70, 52), fill=(255, 255, 255, 50))
        out = Image.alpha_composite(out, highlight)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for color in ("white", "black"):
        for kind in ("pawn", "knight", "bishop", "rook", "queen", "king"):
            path = OUT / f"{color}_{kind}.png"
            draw_piece(kind, color).save(path)
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
