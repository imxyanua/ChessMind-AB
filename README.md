# ChessMind-AB

ChessMind-AB is a chess simulation project that applies Minimax with Alpha-Beta Pruning to select optimal moves, while comparing search efficiency, node reduction, and execution time.

## Stack

- Python 3.11+
- pytest
- tkinter (graphical UI, included with standard Python on Windows)

## Setup

```bash
python -m pip install -e ".[dev]"
```

## Run graphical UI (recommended)

```bash
python -m chessmind_ab gui
```

or simply:

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
3. The AI (Black) replies automatically; panel shows last move, score, nodes, time.
4. Use **New Game** to restart; change **AI depth** (1-5) as needed.
5. In play mode the AI may vary among near-equal best moves, so games feel less repetitive.

## Run tests

```bash
pytest
```

## Terminal helpers (optional)

```bash
python -m chessmind_ab demo
python -m chessmind_ab play --depth 2
```

## Layout

```text
src/chessmind_ab/
  domain/
  search/
  application/
  presentation/   # gui.py + cli.py
tests/
```
