"""Comparison records for local benchmark runs."""

from __future__ import annotations

from operator_workflow_common import phase40_artifact, stable_row_id


def build_benchmark_comparison_history(history: dict, drift: dict) -> dict:
    runs = history.get("benchmark_runs") or []
    latest = runs[-1] if runs else {}
    rows = []
    for entry in drift.get("drift_entries") or []:
        rows.append({
            "benchmark_comparison_id": stable_row_id("BCOMP", latest.get("benchmark_run_id"), entry.get("performance_drift_id")),
            "source_benchmark_run_id": latest.get("benchmark_run_id"),
            "comparison_metric": entry.get("metric"),
            "current_seconds": entry.get("current_seconds"),
            "baseline_seconds": entry.get("baseline_seconds"),
            "drift_level": entry.get("drift_level"),
            "comparison_mode": "current_run_to_local_baseline",
        })
    artifact = phase40_artifact("deterministic_benchmark_comparison_history_v1")
    artifact.update({"benchmark_comparison_history_id": stable_row_id("BCOMPREG", [row["benchmark_comparison_id"] for row in rows]), "comparisons": rows, "summary": {"comparison_count": len(rows)}})
    return artifact
