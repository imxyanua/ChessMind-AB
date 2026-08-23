"""Named ECO-style opening lines used to build the play-mode book.

Lines are UCI move lists (e2e4, g8f6, ...). They are representative
club/master pathways, not a full master database.
"""

from __future__ import annotations

# Each entry: (eco_or_name, [uci_moves...])
ECO_LINES: list[tuple[str, list[str]]] = [
    # Open Games (1.e4 e5)
    ("C60 Ruy Lopez", ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6"]),
    ("C60 Ruy Lopez Berlin", ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6", "e1g1", "f6e4"]),
    ("C50 Italian Game", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3", "g8f6"]),
    ("C50 Italian Giuoco", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "d2d3", "g8f6"]),
    ("C44 Scotch Game", ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "g8f6"]),
    ("C45 Scotch Four Knights", ["e2e4", "e7e5", "g1f3", "b8c6", "b1c3", "g8f6", "d2d4", "e5d4"]),
    ("C46 Four Knights", ["e2e4", "e7e5", "g1f3", "b8c6", "b1c3", "g8f6", "f1b5", "f8b4"]),
    ("C25 Vienna Game", ["e2e4", "e7e5", "b1c3", "g8f6", "f2f4", "d7d5", "f4e5", "f6e4"]),
    ("C30 King's Gambit", ["e2e4", "e7e5", "f2f4", "e5f4", "g1f3", "g7g5", "f1c4", "g5g4"]),
    ("C40 Latvian ideas", ["e2e4", "e7e5", "g1f3", "f7f5", "f3e5", "d8f6", "d2d4", "d7d6"]),
    ("C41 Philidor", ["e2e4", "e7e5", "g1f3", "d7d6", "d2d4", "b8d7", "f1c4", "c7c6"]),
    ("C42 Petrov", ["e2e4", "e7e5", "g1f3", "g8f6", "f3e5", "d7d6", "e5f3", "f6e4"]),
    # Sicilian
    ("B20 Sicilian", ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6"]),
    ("B90 Najdorf setup", ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"]),
    ("B70 Dragon setup", ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "g7g6"]),
    ("B40 Sicilian Kan", ["e2e4", "c7c5", "g1f3", "e7e6", "d2d4", "c5d4", "f3d4", "a7a6"]),
    ("B30 Sicilian Rossolimo", ["e2e4", "c7c5", "g1f3", "b8c6", "f1b5", "g7g6", "e1g1", "f8g7"]),
    ("B22 Alapin", ["e2e4", "c7c5", "c2c3", "g8f6", "e4e5", "f6d5", "d2d4", "c5d4"]),
    ("B27 Sicilian Hyperaccel", ["e2e4", "c7c5", "g1f3", "g7g6", "d2d4", "c5d4", "f3d4", "f8g7"]),
    # French / Caro / Pirc
    ("C00 French", ["e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "g8f6", "c1g5", "f8e7"]),
    ("C02 French Advance", ["e2e4", "e7e6", "d2d4", "d7d5", "e4e5", "c7c5", "c2c3", "b8c6"]),
    ("C11 French Classical", ["e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "g8f6", "e4e5", "f6d7"]),
    ("B10 Caro-Kann", ["e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "c8f5"]),
    ("B12 Caro Advance", ["e2e4", "c7c6", "d2d4", "d7d5", "e4e5", "c8f5", "g1f3", "e7e6"]),
    ("B15 Caro Classical", ["e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "b8d7"]),
    ("B07 Pirc", ["e2e4", "d7d6", "d2d4", "g8f6", "b1c3", "g7g6", "c1e3", "f8g7"]),
    ("B06 Modern", ["e2e4", "g7g6", "d2d4", "f8g7", "b1c3", "d7d6", "f2f4", "g8f6"]),
    ("B01 Scandinavian", ["e2e4", "d7d5", "e4d5", "d8d5", "b1c3", "d5a5", "d2d4", "g8f6"]),
    ("B02 Alekhine", ["e2e4", "g8f6", "e4e5", "f6d5", "d2d4", "d7d6", "g1f3", "c8g4"]),
    # Queen pawn
    ("D06 Queen's Gambit", ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5", "f8e7"]),
    ("D10 Slav", ["d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "d5c4"]),
    ("D30 QGD", ["d2d4", "d7d5", "c2c4", "e7e6", "g1f3", "g8f6", "b1c3", "f8e7"]),
    ("D31 QGD Exchange ideas", ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "c7c6", "c4d5", "e6d5"]),
    ("D35 QGD Capablanca", ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c4d5", "e6d5"]),
    ("D37 QGD 5.Bf4", ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "g1f3", "f8e7", "c1f4"]),
    ("D43 Semi-Slav", ["d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "e7e6"]),
    ("D70 Grunfeld ideas", ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5", "c4d5", "f6d5"]),
    ("E60 King's Indian", ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6"]),
    ("E90 KID Classical", ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6", "g1f3", "e8g8"]),
    ("E20 Nimzo-Indian", ["d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "e2e3", "e8g8"]),
    ("E00 Queen's Indian ideas", ["d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "b7b6", "g2g3", "c8b7"]),
    ("A40 Modern Defense vs d4", ["d2d4", "g7g6", "c2c4", "f8g7", "b1c3", "d7d6", "e2e4", "g8f6"]),
    ("A80 Dutch", ["d2d4", "f7f5", "g2g3", "g8f6", "f1g2", "e7e6", "g1f3", "f8e7"]),
    ("D00 London System", ["d2d4", "d7d5", "g1f3", "g8f6", "c1f4", "c7c5", "e2e3", "b8c6"]),
    ("D02 London vs ...Nf6", ["d2d4", "g8f6", "g1f3", "d7d5", "c1f4", "c7c5", "e2e3", "b8c6"]),
    ("A45 Trompowsky", ["d2d4", "g8f6", "c1g5", "f6e4", "g5f4", "c7c5", "f2f3", "e4f6"]),
    ("D08 Albin ideas", ["d2d4", "d7d5", "c2c4", "e7e5", "d4e5", "d5d4", "g1f3", "b8c6"]),
    ("E04 Catalan ideas", ["d2d4", "g8f6", "c2c4", "e7e6", "g2g3", "d7d5", "f1g2", "f8e7"]),
    # Flank
    ("A10 English", ["c2c4", "e7e5", "b1c3", "g8f6", "g1f3", "b8c6", "g2g3", "f8b4"]),
    ("A20 English ...e5", ["c2c4", "e7e5", "g2g3", "g8f6", "f1g2", "b8c6", "b1c3", "f8c5"]),
    ("A15 English ...Nf6", ["c2c4", "g8f6", "g1f3", "g7g6", "g2g3", "f8g7", "f1g2", "d7d6", "e1g1"]),
    ("A30 English Symmetrical", ["c2c4", "c7c5", "g1f3", "g8f6", "g2g3", "b7b6", "f1g2", "c8b7"]),
    ("A04 Reti", ["g1f3", "d7d5", "c2c4", "e7e6", "g2g3", "g8f6", "f1g2", "f8e7"]),
    ("A07 King's Indian Attack", ["g1f3", "d7d5", "g2g3", "g8f6", "f1g2", "c7c6", "e1g1", "c8g4"]),
    ("A00 Larsen", ["b2b3", "e7e5", "c1b2", "b8c6", "e2e3", "g8f6", "f1b5", "d7d6"]),
    ("A00 Bird", ["f2f4", "d7d5", "g1f3", "g8f6", "e2e3", "c7c5", "b2b3", "b8c6"]),
    # Extra short branches for variety at ply 1-4
    ("C20 Center Game", ["e2e4", "e7e5", "d2d4", "e5d4", "d1d4", "b8c6", "d4e3", "g8f6"]),
    ("C23 Bishop's Opening", ["e2e4", "e7e5", "f1c4", "g8f6", "d2d3", "c7c6", "g1f3", "d7d5"]),
    ("C21 Danish ideas", ["e2e4", "e7e5", "d2d4", "e5d4", "c2c3", "d4c3", "b1c3", "f8b4"]),
    ("B21 Smith-Morra ideas", ["e2e4", "c7c5", "d2d4", "c5d4", "c2c3", "d4c3", "b1c3", "b8c6"]),
    ("B50 Sicilian 2...d6", ["e2e4", "c7c5", "g1f3", "d7d6", "f1b5", "c8d7", "b5d7", "d8d7"]),
    ("C00 French 2.d3", ["e2e4", "e7e6", "d2d3", "d7d5", "b1d2", "g8f6", "g1f3", "c7c5"]),
    ("D20 QGA", ["d2d4", "d7d5", "c2c4", "d5c4", "g1f3", "g8f6", "e2e3", "e7e6"]),
    ("A50 Indian ...e6", ["d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "b7b6", "g2g3", "c8a6"]),
    ("A53 Old Indian", ["d2d4", "g8f6", "c2c4", "d7d6", "b1c3", "b8d7", "e2e4", "e7e5"]),
    ("A40 Englund ideas", ["d2d4", "e7e5", "d4e5", "b8c6", "g1f3", "d8e7", "c1f4", "e7b4"]),
    ("C44 Ponziani", ["e2e4", "e7e5", "g1f3", "b8c6", "c2c3", "g8f6", "d2d4", "f6e4"]),
    ("C55 Two Knights", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "d2d3", "f8e7"]),
    ("C57 Two Knights Fried", ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5"]),
    ("B12 Caro Fantasy", ["e2e4", "c7c6", "d2d4", "d7d5", "f2f3", "d5e4", "f3e4", "e7e5"]),
    ("D70 Neo-Grunfeld ideas", ["d2d4", "g8f6", "c2c4", "g7g6", "g2g3", "d7d5", "f1g2", "f8g7"]),
    ("E10 Blumenfeld ideas", ["d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "c7c5", "d4d5", "b7b5"]),
    ("A36 English Botvinnik", ["c2c4", "g7g6", "b1c3", "f8g7", "g2g3", "e7e5", "f1g2", "d7d6"]),
    ("A13 English ...e6", ["c2c4", "e7e6", "g1f3", "d7d5", "g2g3", "g8f6", "f1g2", "f8e7"]),
    ("A05 Reti ...Nf6", ["g1f3", "g8f6", "g2g3", "g7g6", "f1g2", "f8g7", "e1g1", "d7d6"]),
]


def iter_eco_lines() -> list[tuple[str, list[str]]]:
    return list(ECO_LINES)
