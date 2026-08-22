"""Search metrics shared by Minimax and Alpha-Beta."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SearchStatistics:
    nodes_visited: int = 0
    evaluated_leaf_nodes: int = 0
    terminal_nodes: int = 0
    generated_moves: int = 0
    cutoffs: int = 0
    max_depth_reached: int = 0
    execution_time_ms: float = 0.0
