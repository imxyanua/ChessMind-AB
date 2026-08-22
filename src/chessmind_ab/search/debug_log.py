"""Optional search debug logging (disabled by default for fair benchmarks)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TextIO


@dataclass(frozen=True, slots=True)
class SearchLogEvent:
    depth: int
    move: str | None
    alpha: float | None
    beta: float | None
    score: int | None
    cutoff: bool


_ENABLED = False
_SINKS: list[Callable[[SearchLogEvent], None]] = []


def set_debug_search(enabled: bool) -> None:
    global _ENABLED
    _ENABLED = bool(enabled)


def is_debug_search_enabled() -> bool:
    return _ENABLED


def configure_from_env() -> None:
    value = os.environ.get("CHESSMIND_DEBUG_SEARCH", "").strip().lower()
    set_debug_search(value in {"1", "true", "yes", "on"})


def add_sink(callback: Callable[[SearchLogEvent], None]) -> None:
    _SINKS.append(callback)


def clear_sinks() -> None:
    _SINKS.clear()


def default_stderr_sink(event: SearchLogEvent) -> None:
    write_event(event, sys.stderr)


def write_event(event: SearchLogEvent, stream: TextIO) -> None:
    stream.write(
        "search_debug"
        f" depth={event.depth}"
        f" move={event.move or '-'}"
        f" alpha={_fmt(event.alpha)}"
        f" beta={_fmt(event.beta)}"
        f" score={event.score if event.score is not None else '-'}"
        f" cutoff={int(event.cutoff)}\n"
    )


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    if value == float("inf"):
        return "+inf"
    if value == float("-inf"):
        return "-inf"
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def log_search(
    *,
    depth: int,
    move: str | None = None,
    alpha: float | None = None,
    beta: float | None = None,
    score: int | None = None,
    cutoff: bool = False,
) -> None:
    if not _ENABLED:
        return
    event = SearchLogEvent(
        depth=depth,
        move=move,
        alpha=alpha,
        beta=beta,
        score=score,
        cutoff=cutoff,
    )
    if not _SINKS:
        default_stderr_sink(event)
        return
    for sink in _SINKS:
        sink(event)


def move_label(move) -> str:
    text = (
        f"{move.from_position.to_chess_notation()}"
        f"{move.to_position.to_chess_notation()}"
    )
    if move.promotion_piece is not None:
        text += f"={move.promotion_piece.name[0]}"
    return text
