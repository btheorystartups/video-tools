"""Deterministic longitudinal trend analysis over historical run snapshots."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id, utc_now_iso


TREND_METRICS = {
    "readiness": ["readiness", "score"],
    "continuity": ["key_metrics", "ambiguity_adjusted_continuity"],
    "contradiction_pressure": ["key_metrics", "false_positive_boundary_ratio"],
    "rhetorical_coherence": ["key_metrics", "rhetorical_balance_score"],
    "argument_completeness": ["key_metrics", "argument_completeness_score"],
    "callback_quality": ["key_metrics", "callback_resolution_quality"],
    "visual_continuity": ["key_metrics", "visual_continuity_score"],
    "integrity_scores": ["key_metrics", "artifact_integrity_score"],
    "graph_consistency": ["key_metrics", "graph_consistency_score"],
    "recommendation_confidence": ["key_metrics", "quality_scores", "recommendation_confidence"],
}


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _get(row: dict, path: list[str]) -> Any:
    value: Any = row
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _series(snapshots: list[dict], path: list[str]) -> list[dict]:
    rows = []
    for index, snapshot in enumerate(snapshots):
        value = _num(_get(snapshot, path))
        if value is not None:
            rows.append({"index": index, "run_id": snapshot.get("run_id"), "value": round(value, 3)})
    return rows


def classify_trend(values: list[float]) -> str:
    if len(values) < 3:
        return "inconclusive"
    delta = values[-1] - values[0]
    volatility = pstdev(values) if len(values) > 1 else 0.0
    step_changes = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
    if volatility >= 0.14 or any(change >= 0.22 for change in step_changes):
        return "volatile"
    if delta >= 0.08:
        return "improving"
    if delta <= -0.08:
        return "degrading"
    return "stable"


def build_trend_analysis(snapshots: list[dict]) -> dict:
    trends = []
    for metric, path in TREND_METRICS.items():
        rows = _series(snapshots, path)
        values = [row["value"] for row in rows]
        trend = classify_trend(values)
        trends.append(
            {
                "trend_id": deterministic_id("trend", metric, [row.get("run_id") for row in rows], values, length=16),
                "metric": metric,
                "values": rows,
                "classification": trend,
                "first_value": values[0] if values else None,
                "latest_value": values[-1] if values else None,
                "delta": round(values[-1] - values[0], 3) if len(values) >= 2 else None,
                "mean": round(mean(values), 3) if values else None,
                "volatility": round(pstdev(values), 3) if len(values) > 1 else 0.0 if values else None,
            }
        )
    counts: dict[str, int] = {}
    for row in trends:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    return {
        "trend_analysis_version": "1.0",
        "analysis_status": STATUS_COMPLETE if len(snapshots) >= 3 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "tracked_run_count": len(snapshots),
        "trend_windows": [{"window": "all_available_runs", "run_count": len(snapshots)}],
        "trends": trends,
        "trend_class_counts": dict(sorted(counts.items())),
        "limitations": [
            "Trends are deterministic heuristics over retained local run snapshots.",
            "At least three comparable runs are required for stronger longitudinal classification.",
        ],
    }
