"""Deterministic local empirical benchmark history."""

from __future__ import annotations

from operator_workflow_common import benchmark_links, phase40_artifact, render_registry_page, stable_row_id


def build_empirical_benchmark_history(outputs: dict) -> dict:
    profile_entries = (outputs.get("performance_profile_registry") or {}).get("profile_entries") or []
    artifact_counts = _artifact_counts(outputs)
    run = {
        "benchmark_run_id": stable_row_id("EBRUN", [(row.get("profile_type"), row.get("estimated_seconds")) for row in profile_entries], artifact_counts),
        "run_label": "current_local_deterministic_run",
        "validation_timing_seconds": _sum(outputs, "validation_timing_registry", "timing_entries", "estimated_validation_seconds"),
        "dashboard_generation_seconds": _sum(outputs, "dashboard_render_registry", "render_entries", "estimated_render_seconds"),
        "queue_generation_seconds": _profile(profile_entries, "queue_generation"),
        "rebuild_timing_seconds": _sum(outputs, "rebuild_cost_registry", "rebuild_costs", "estimated_cost_units"),
        "corpus_size": (outputs.get("corpus_index") or {}).get("video_count") or 0,
        "artifact_counts": artifact_counts,
        "nondeterministic_benchmarking_used": False,
    }
    artifact = phase40_artifact("deterministic_empirical_benchmark_history_v1")
    artifact.update({"empirical_benchmark_history_id": stable_row_id("EBHIST", run["benchmark_run_id"]), "benchmark_runs": [run], "summary": {"benchmark_run_count": 1, "total_artifact_count": sum(artifact_counts.values())}})
    return artifact


def render_benchmark_history_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("empirical_benchmark_history") or {}).get("benchmark_runs") or []
    return {"benchmark_history_dashboard.html": render_registry_page("Benchmark History Dashboard", "Benchmarks", "benchmark_history_dashboard.html", rows, ["run_label", "validation_timing_seconds", "dashboard_generation_seconds", "queue_generation_seconds", "rebuild_timing_seconds", "corpus_size"], "benchmark_run_id", [("Runs", len(rows))], benchmark_links(""))}


def _sum(outputs: dict, key: str, field: str, value: str) -> float:
    return round(sum(float(row.get(value) or 0) for row in (outputs.get(key) or {}).get(field) or []), 3)


def _profile(rows: list[dict], profile_type: str) -> float:
    return round(sum(float(row.get("estimated_seconds") or 0) for row in rows if row.get("profile_type") == profile_type), 3)


def _artifact_counts(outputs: dict) -> dict:
    return {
        "queues": sum(len((outputs.get(key) or {}).get("queue_items") or []) for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue"]),
        "dashboards": len((outputs.get("dashboard_render_registry") or {}).get("render_entries") or []),
        "validation_entries": len((outputs.get("validation_index") or {}).get("validation_entries") or []),
        "benchmark_profiles": len((outputs.get("performance_profile_registry") or {}).get("profile_entries") or []),
    }
