"""Persistent append-only benchmark lineage for Phase 41."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import read_json
from phase41_longitudinal_common import phase41_artifact, queue_count, render_longitudinal_page, stable_row_id


def build_persistent_benchmark_lineage(outputs: dict, prior_lineage: dict | None = None) -> dict:
    history_run = ((outputs.get("empirical_benchmark_history") or {}).get("benchmark_runs") or [{}])[-1]
    artifact_counts = history_run.get("artifact_counts") or {}
    entry = {
        "benchmark_lineage_entry_id": stable_row_id("PBL", history_run.get("benchmark_run_id"), artifact_counts, queue_count(outputs)),
        "benchmark_run_id": history_run.get("benchmark_run_id"),
        "run_label": history_run.get("run_label", "current_local_deterministic_run"),
        "validation_timing_seconds": float(history_run.get("validation_timing_seconds") or 0),
        "rebuild_timing_seconds": float(history_run.get("rebuild_timing_seconds") or 0),
        "dashboard_generation_seconds": float(history_run.get("dashboard_generation_seconds") or 0),
        "queue_generation_seconds": float(history_run.get("queue_generation_seconds") or 0),
        "artifact_total_count": sum(int(value or 0) for value in artifact_counts.values()),
        "queue_total_count": queue_count(outputs),
        "dashboard_count": int(artifact_counts.get("dashboards") or 0),
        "operational_workload_units": round(queue_count(outputs) + float(history_run.get("rebuild_timing_seconds") or 0), 3),
        "append_only_entry": True,
        "nondeterministic_benchmarking_used": False,
    }
    prior_entries = list((prior_lineage or {}).get("lineage_entries") or [])
    if not any(row.get("benchmark_lineage_entry_id") == entry["benchmark_lineage_entry_id"] for row in prior_entries):
        prior_entries.append(entry)
    artifact = phase41_artifact("deterministic_persistent_benchmark_lineage_v1")
    artifact.update(
        {
            "persistent_benchmark_lineage_id": stable_row_id("PBLREG", [row.get("benchmark_lineage_entry_id") for row in prior_entries]),
            "lineage_entries": prior_entries,
            "summary": {
                "lineage_entry_count": len(prior_entries),
                "latest_artifact_total_count": entry["artifact_total_count"],
                "latest_queue_total_count": entry["queue_total_count"],
                "append_only_history_preserved": True,
            },
        }
    )
    return artifact


def load_prior_persistent_benchmark_lineage(output_dir: Path) -> dict:
    path = output_dir / "longitudinal" / "persistent_benchmark_lineage.json"
    if path.exists():
        return read_json(path)
    return {}


def render_benchmark_lineage_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("persistent_benchmark_lineage") or {}).get("lineage_entries") or []
    return render_longitudinal_page(
        "Benchmark Lineage Dashboard",
        "benchmark_lineage_dashboard.html",
        rows,
        ["run_label", "validation_timing_seconds", "rebuild_timing_seconds", "artifact_total_count", "queue_total_count"],
        "benchmark_lineage_entry_id",
        [("Lineage entries", len(rows))],
    )

