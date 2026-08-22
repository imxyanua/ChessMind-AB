# ChessMind-AB

ChessMind-AB is a chess simulation project that applies Minimax with Alpha-Beta Pruning to select optimal moves, while comparing search efficiency, node reduction, and execution time.

## Stack

- Python 3.11+
- pytest
- tkinter GUI with PNG piece sprites
- Pillow (optional, only to regenerate piece sprites)

## Setup

```bash
python -m pip install -e ".[dev]"
```

## Run graphical UI (recommended)

```bash
python -m chessmind_ab gui
```

or:

```bash
python -m chessmind_ab
```

Choose an Elo difficulty mode:

```bash
python -m chessmind_ab gui --difficulty medium
```

Modes: `beginner` (~600), `easy` (~800), `medium` (~1000), `hard` (~1200), `expert` (~1400).

AI search runs in a **background thread** so the window should stay responsive while thinking.

How to play:

1. A window opens with three columns: **board**, **info/controls**, and **SAN move history**.
2. Pick a **Difficulty** (Elo mode) instead of raw search depth.
3. Click a white piece, then a marked destination (dot/ring); pieces **slide** to the target.
4. Switch **Board/UI themes**, view **captured pieces** in the info column.
5. **Undo** reverts the last player+AI turn.
6. **Copy PGN** / **Save PGN** exports the game in Standard Algebraic Notation.

Refresh piece sprites (Wikipedia set via chessboardjs assets):

```bash
python scripts/fetch_piece_sprites.py
```

## Run tests

```bash
pytest
```

## Terminal helpers (optional)

```bash
python -m chessmind_ab demo
python -m chessmind_ab play --depth 2
```

## Benchmark report

Compare Minimax / AlphaBeta / AlphaBeta+Ordering (deterministic):

```bash
python -m chessmind_ab benchmark --depth 2 --out benchmark_results.csv
```

Use depth 1-2 for quick runs; higher depths get slow because of quiescence.

## Layout

```text
src/chessmind_ab/
  assets/pieces/   # PNG sprites
  domain/
  search/
  application/
  presentation/
tests/
```
