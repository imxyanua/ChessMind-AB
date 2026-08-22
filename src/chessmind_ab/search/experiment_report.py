"""Experimental report: CSV + Markdown analysis for thesis hypotheses H1-H5."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from chessmind_ab.search.benchmark import (
    BenchmarkRow,
    format_benchmark,
    run_benchmark,
    write_benchmark_csv,
)

_MINIMAX = "Minimax"
_AB = "AlphaBeta"
_ABO = "AlphaBeta+Ordering"


@dataclass(frozen=True, slots=True)
class HypothesisResult:
    key: str
    title: str
    supported: bool | None
    detail: str


@dataclass(frozen=True, slots=True)
class ExperimentReport:
    rows: list[BenchmarkRow]
    hypotheses: list[HypothesisResult]
    markdown: str
    csv_text: str


def _index_rows(
    rows: list[BenchmarkRow],
) -> dict[tuple[str, int, str], BenchmarkRow]:
    return {(row.name, row.depth, row.algorithm): row for row in rows}


def analyze_hypotheses(rows: list[BenchmarkRow]) -> list[HypothesisResult]:
    by_key = _index_rows(rows)
    positions = sorted({row.name for row in rows})
    depths = sorted({row.depth for row in rows})

    # H1 — same score across algorithms for each (position, depth)
    h1_ok = True
    h1_notes: list[str] = []
    for pos in positions:
        for depth in depths:
            scores = []
            for algo in (_MINIMAX, _AB, _ABO):
                row = by_key.get((pos, depth, algo))
                if row is None:
                    continue
                scores.append(row.score)
            if len(scores) >= 2 and len(set(scores)) != 1:
                h1_ok = False
                h1_notes.append(f"{pos}@d{depth}: scores={scores}")
    h1 = HypothesisResult(
        key="H1",
        title="Correctness (MinimaxScore = AlphaBetaScore)",
        supported=h1_ok,
        detail=(
            "All algorithms returned equal scores on every position/depth."
            if h1_ok
            else "Score mismatch: " + "; ".join(h1_notes)
        ),
    )

    # H2 — AlphaBeta nodes <= Minimax nodes
    h2_pass = 0
    h2_total = 0
    for pos in positions:
        for depth in depths:
            mm = by_key.get((pos, depth, _MINIMAX))
            ab = by_key.get((pos, depth, _AB))
            if mm is None or ab is None:
                continue
            h2_total += 1
            if ab.nodes <= mm.nodes:
                h2_pass += 1
    h2 = HypothesisResult(
        key="H2",
        title="Search reduction (NodesAlphaBeta <= NodesMinimax)",
        supported=(h2_pass == h2_total and h2_total > 0),
        detail=f"Held on {h2_pass}/{h2_total} position-depth pairs.",
    )

    # H3 — Ordering nodes <= plain AlphaBeta on majority
    h3_pass = 0
    h3_total = 0
    for pos in positions:
        for depth in depths:
            ab = by_key.get((pos, depth, _AB))
            abo = by_key.get((pos, depth, _ABO))
            if ab is None or abo is None:
                continue
            h3_total += 1
            if abo.nodes <= ab.nodes:
                h3_pass += 1
    h3_supported: bool | None
    if h3_total == 0:
        h3_supported = None
    else:
        h3_supported = h3_pass >= (h3_total + 1) // 2
    h3 = HypothesisResult(
        key="H3",
        title="Move ordering (NodesABOrdered <= NodesAB on majority)",
        supported=h3_supported,
        detail=f"Ordering reduced or matched nodes on {h3_pass}/{h3_total} pairs.",
    )

    # H4 — nodes grow with depth
    h4_supported: bool | None = None
    h4_detail = "Need at least two depths to evaluate growth."
    if len(depths) >= 2:
        d_lo, d_hi = depths[0], depths[-1]
        grew = 0
        total = 0
        for pos in positions:
            for algo in (_MINIMAX, _AB, _ABO):
                lo = by_key.get((pos, d_lo, algo))
                hi = by_key.get((pos, d_hi, algo))
                if lo is None or hi is None:
                    continue
                total += 1
                if hi.nodes > lo.nodes:
                    grew += 1
        h4_supported = grew == total and total > 0
        h4_detail = (
            f"Nodes increased from depth {d_lo} to {d_hi} "
            f"on {grew}/{total} algorithm-position pairs."
        )
    h4 = HypothesisResult(
        key="H4",
        title="Depth (node count grows quickly with depth)",
        supported=h4_supported,
        detail=h4_detail,
    )

    # H5 — Alpha-Beta benefit clearer on larger trees (deeper depth)
    h5_supported: bool | None = None
    h5_detail = "Need at least two depths to compare pruning benefit."
    if len(depths) >= 2:
        d_lo, d_hi = depths[0], depths[-1]

        def _mean_reduction(depth: int) -> float | None:
            ratios: list[float] = []
            for pos in positions:
                mm = by_key.get((pos, depth, _MINIMAX))
                ab = by_key.get((pos, depth, _AB))
                if mm is None or ab is None or mm.nodes <= 0:
                    continue
                ratios.append(1.0 - (ab.nodes / mm.nodes))
            if not ratios:
                return None
            return sum(ratios) / len(ratios)

        r_lo = _mean_reduction(d_lo)
        r_hi = _mean_reduction(d_hi)
        if r_lo is None or r_hi is None:
            h5_detail = "Insufficient Minimax/AlphaBeta pairs for reduction ratio."
        else:
            h5_supported = r_hi >= r_lo
            h5_detail = (
                f"Mean node reduction vs Minimax: "
                f"depth {d_lo} = {r_lo:.1%}, depth {d_hi} = {r_hi:.1%}."
            )
    h5 = HypothesisResult(
        key="H5",
        title="Alpha-Beta benefit (clearer on larger trees)",
        supported=h5_supported,
        detail=h5_detail,
    )

    return [h1, h2, h3, h4, h5]


def _status_label(supported: bool | None) -> str:
    if supported is True:
        return "SUPPORTED"
    if supported is False:
        return "NOT SUPPORTED"
    return "INCONCLUSIVE"


def _summary_table(rows: list[BenchmarkRow]) -> str:
    # Aggregate mean nodes/time per algorithm at each depth.
    buckets: dict[tuple[int, str], list[BenchmarkRow]] = defaultdict(list)
    for row in rows:
        buckets[(row.depth, row.algorithm)].append(row)

    lines = [
        "| Depth | Algorithm | Mean nodes | Mean cutoffs | Mean time (ms) |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    for depth, algo in sorted(buckets.keys(), key=lambda item: (item[0], item[1])):
        group = buckets[(depth, algo)]
        mean_nodes = sum(r.nodes for r in group) / len(group)
        mean_cut = sum(r.cutoffs for r in group) / len(group)
        mean_time = sum(r.time_ms for r in group) / len(group)
        lines.append(
            f"| {depth} | {algo} | {mean_nodes:.1f} | {mean_cut:.1f} | {mean_time:.2f} |"
        )
    return "\n".join(lines)


def _raw_table(rows: list[BenchmarkRow]) -> str:
    lines = [
        "| Position | Algorithm | Depth | Nodes | Cutoffs | Score | Best | Time (ms) |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in sorted(rows, key=lambda r: (r.depth, r.name, r.algorithm)):
        lines.append(
            f"| {row.name} | {row.algorithm} | {row.depth} | {row.nodes} | "
            f"{row.cutoffs} | {row.score} | {row.best_move} | {row.time_ms:.2f} |"
        )
    return "\n".join(lines)


def render_markdown(
    rows: list[BenchmarkRow],
    hypotheses: list[HypothesisResult],
    *,
    title: str = "ChessMind-AB Experimental Report",
) -> str:
    depths = sorted({row.depth for row in rows})
    positions = sorted({row.name for row in rows})
    parts = [
        f"# {title}",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Depths: {', '.join(str(d) for d in depths)}",
        f"- Positions: {', '.join(positions)}",
        "- Algorithms: Minimax, AlphaBeta, AlphaBeta+Ordering (deterministic)",
        "",
        "## Hypothesis results",
        "",
    ]
    for hyp in hypotheses:
        parts.append(f"### {hyp.key} — {hyp.title}")
        parts.append("")
        parts.append(f"- Verdict: **{_status_label(hyp.supported)}**")
        parts.append(f"- Detail: {hyp.detail}")
        parts.append("")

    parts.extend(
        [
            "## Aggregate summary",
            "",
            _summary_table(rows),
            "",
            "## Raw measurements",
            "",
            _raw_table(rows),
            "",
            "## Notes",
            "",
            "- Correctness compares search scores, not play Elo.",
            "- Timing depends on hardware; node/cutoff counts are the primary metrics.",
            "- Quiescence may expand leaves beyond the nominal depth.",
            "",
        ]
    )
    return "\n".join(parts)


def build_report(depths: list[int] | None = None) -> ExperimentReport:
    use_depths = depths or [1, 2]
    rows: list[BenchmarkRow] = []
    for depth in use_depths:
        if depth < 1:
            raise ValueError("depth must be >= 1")
        rows.extend(run_benchmark(depth=depth))
    hypotheses = analyze_hypotheses(rows)
    markdown = render_markdown(rows, hypotheses)
    return ExperimentReport(
        rows=rows,
        hypotheses=hypotheses,
        markdown=markdown,
        csv_text=format_benchmark(rows) + "\n",
    )


def write_report(
    output_dir: Path,
    depths: list[int] | None = None,
    *,
    csv_name: str = "experiment_results.csv",
    md_name: str = "experiment_report.md",
) -> tuple[Path, Path, ExperimentReport]:
    report = build_report(depths=depths)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = write_benchmark_csv(report.rows, output_dir / csv_name)
    md_path = output_dir / md_name
    md_path.write_text(report.markdown, encoding="utf-8")
    return csv_path, md_path, report
