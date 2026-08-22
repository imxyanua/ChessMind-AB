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

Optional AI depth:

```bash
python -m chessmind_ab gui --depth 3
```

How to play:

1. A window opens with the chess board and an info panel.
2. Click a white piece, then click a marked destination (dot/ring).
3. The AI (Black) replies automatically.
4. Use the panel to switch **Board/UI themes**, change **AI depth**, view **captured pieces** and **move list**.
5. **Undo** reverts the last player+AI turn.
6. In play mode the AI may vary among near-equal best moves.

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
