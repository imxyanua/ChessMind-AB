# ChessMind-AB

ChessMind-AB is a chess simulation project that applies Minimax with Alpha-Beta Pruning to select optimal moves, while comparing search efficiency, node reduction, and execution time.

## Stack

- Python 3.11+
- pytest
- **PySide6** desktop GUI with PNG piece sprites
- Pillow (optional, only to regenerate piece sprites)

Core rules now include **castling**, **en passant**, and draw detection (**threefold**, **fifty-move**, **insufficient material**), in addition to the original mandatory set.

## Setup

```bash
python -m pip install -e ".[dev]"
```

## Run graphical UI (recommended)

```bash
python -m chessmind_ab gui
```

Choose an Elo difficulty mode:

```bash
python -m chessmind_ab gui --difficulty medium
```

Modes (strength gaps are intentional): `beginner` (~600, depth 1, no book), `easy` (~800, depth 2), `medium` (~1000, depth 3), `hard` (~1200, depth 4), `expert` (~1400, depth 6, always best root move).

Play mode uses **iterative deepening** with a soft time budget per difficulty (max depth still capped by the preset). Weaker tiers keep a wider root **diversity** window so they often play near-best instead of best. Easy+ use an **ECO-style opening book**; Beginner skips the book on purpose. Benchmarks keep fixed-depth search for fair comparisons.

AI search runs in a **background thread** so the window should stay responsive while thinking.

How to play:

1. A window opens with three columns: **board**, **info/controls**, and **SAN move history**.
2. Pick **Mode**: **Player vs AI** or **AI vs AI**.
3. In Player vs AI: choose **Play as** White or Black (board flips when you play Black; AI moves first) and one **Difficulty**.
4. In AI vs AI: set **White AI** / **Black AI** Elo (same or different), **Speed**, then **Start** / **Pause** / **Stop** / **Step**.
5. Click your piece, then a marked destination (dot/ring); pieces **slide** to the target (including castling rook).
6. Switch **Board/UI themes**, view **captured pieces** in the info column.
7. **Undo** reverts the last player+AI turn (or one ply in AI vs AI).
8. **Copy PGN** / **Save PGN** exports the game in Standard Algebraic Notation.

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

## Benchmark / experimental report

Compare Minimax / AlphaBeta / AlphaBeta+Ordering (deterministic):

```bash
python -m chessmind_ab benchmark --depth 2 --out benchmark_results.csv
python -m chessmind_ab benchmark --depth 2 --tt --out benchmark_results.csv
```

`--tt` adds `AlphaBeta+Ordering+TT` for optional transposition-table comparison. Play mode already uses a TT.

Generate thesis-style CSV + Markdown (hypotheses H1–H5):

```bash
python -m chessmind_ab report --depths 1,2 --report-dir experiment_out
```

Use **`--depths 1,2`** so H4/H5 can be judged (a single depth leaves them inconclusive).
Higher depths get slow because of quiescence. Generated files stay local (`experiment_out/` is gitignored).

How to read the verdicts:

| Hypothesis | Meaning |
|------------|---------|
| H1 Correctness | Minimax score equals Alpha-Beta score |
| H2 Search reduction | Alpha-Beta visits ≤ Minimax nodes |
| H3 Move ordering | Ordered AB visits ≤ plain AB on a majority of cases |
| H4 Depth | Node count grows when depth increases |
| H5 Alpha-Beta benefit | Mean pruning gain is clearer on the deeper search |

Example local run (`--depths 1,2`): H1–H5 all **SUPPORTED** (H5 ~24% reduction at depth 1 vs ~77% at depth 2).

Optional Alpha-Beta debug logging (off by default; forced off for `benchmark`/`report`):

```bash
python -m chessmind_ab play --debug-search
# or: set CHESSMIND_DEBUG_SEARCH=1
```

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
