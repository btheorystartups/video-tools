"""Local deterministic benchmark baselines."""

from __future__ import annotations

from operator_workflow_common import benchmark_links, phase40_artifact, render_registry_page, stable_row_id


def build_local_benchmark_baselines(history: dict) -> dict:
    runs = history.get("benchmark_runs") or []
    fields = ["validation_timing_seconds", "dashboard_generation_seconds", "queue_generation_seconds", "rebuild_timing_seconds"]
    rows = []
    for field in fields:
        values = [float(run.get(field) or 0) for run in runs]
        baseline = round(sum(values) / len(values), 3) if values else 0.0
        rows.append({"local_benchmark_baseline_id": stable_row_id("LBASE", field, baseline), "metric": field, "baseline_seconds": baseline, "sample_count": len(values), "baseline_mode": "local_deterministic_history", "nondeterministic_benchmarking_used": False})
    artifact = phase40_artifact("deterministic_local_benchmark_baselines_v1")
    artifact.update({"local_benchmark_baselines_id": stable_row_id("LBASEREG", [row["local_benchmark_baseline_id"] for row in rows]), "baselines": rows, "summary": {"baseline_count": len(rows)}})
    return artifact


def render_empirical_baseline_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("local_benchmark_baselines") or {}).get("baselines") or []
    return {"empirical_baseline_dashboard.html": render_registry_page("Empirical Baseline Dashboard", "Benchmarks", "empirical_baseline_dashboard.html", rows, ["metric", "baseline_seconds", "sample_count", "baseline_mode"], "local_benchmark_baseline_id", [("Baselines", len(rows))], benchmark_links(""))}
