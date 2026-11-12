"""Repeated deterministic benchmark snapshots."""

from __future__ import annotations

from operator_workflow_common import benchmark_links, phase40_artifact, render_registry_page, stable_row_id


def build_repeated_benchmark_snapshots(history: dict) -> dict:
    runs = history.get("benchmark_runs") or []
    snapshots = []
    for index, run in enumerate(runs, 1):
        snapshots.append({
            "benchmark_snapshot_id": stable_row_id("RBSNAP", index, run.get("benchmark_run_id")),
            "snapshot_index": index,
            "source_benchmark_run_id": run.get("benchmark_run_id"),
            "validation_timing_seconds": run.get("validation_timing_seconds", 0),
            "dashboard_generation_seconds": run.get("dashboard_generation_seconds", 0),
            "queue_generation_seconds": run.get("queue_generation_seconds", 0),
            "rebuild_timing_seconds": run.get("rebuild_timing_seconds", 0),
            "deterministic_snapshot": True,
        })
    artifact = phase40_artifact("deterministic_repeated_benchmark_snapshots_v1")
    artifact.update({"repeated_benchmark_snapshots_id": stable_row_id("RBSNAPREG", [row["benchmark_snapshot_id"] for row in snapshots]), "snapshots": snapshots, "summary": {"snapshot_count": len(snapshots)}})
    return artifact


def render_repeated_benchmark_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("repeated_benchmark_snapshots") or {}).get("snapshots") or []
    return {"repeated_benchmark_dashboard.html": render_registry_page("Repeated Benchmark Dashboard", "Benchmarks", "repeated_benchmark_dashboard.html", rows, ["snapshot_index", "validation_timing_seconds", "dashboard_generation_seconds", "queue_generation_seconds", "rebuild_timing_seconds"], "benchmark_snapshot_id", [("Snapshots", len(rows))], benchmark_links(""))}
