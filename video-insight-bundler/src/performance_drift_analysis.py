"""Performance drift analysis across deterministic benchmark snapshots."""

from __future__ import annotations

from operator_workflow_common import benchmark_links, phase40_artifact, render_registry_page, risk_level, stable_row_id


def build_performance_drift_registry(history: dict, baselines: dict) -> dict:
    latest = ((history.get("benchmark_runs") or [{}])[-1])
    baseline_by_metric = {row.get("metric"): row for row in baselines.get("baselines") or []}
    metrics = [
        ("validation_slowdown", "validation_timing_seconds"),
        ("dashboard_rendering_growth", "dashboard_generation_seconds"),
        ("queue_growth_impact", "queue_generation_seconds"),
        ("artifact_explosion_impact", "rebuild_timing_seconds"),
        ("dependency_depth_growth", "rebuild_timing_seconds"),
    ]
    rows = []
    for drift_type, metric in metrics:
        current = float(latest.get(metric) or 0)
        baseline = float((baseline_by_metric.get(metric) or {}).get("baseline_seconds") or 0)
        delta = round(current - baseline, 3)
        ratio = round(current / baseline, 3) if baseline else (1.0 if current else 0.0)
        rows.append({"performance_drift_id": stable_row_id("PDRIFT", drift_type, current, baseline), "drift_type": drift_type, "metric": metric, "current_seconds": current, "baseline_seconds": baseline, "delta_seconds": delta, "drift_ratio": ratio, "drift_level": risk_level(min(1.0, max(0.0, ratio - 1.0))), "deterministic_analysis": True})
    artifact = phase40_artifact("deterministic_performance_drift_analysis_v1")
    artifact.update({"performance_drift_registry_id": stable_row_id("PDRIFTREG", [row["performance_drift_id"] for row in rows]), "drift_entries": rows, "summary": {"drift_entry_count": len(rows), "high_drift_count": sum(1 for row in rows if row["drift_level"] == "high")}})
    return artifact


def render_performance_drift_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("performance_drift_registry") or {}).get("drift_entries") or []
    return {"performance_drift_dashboard.html": render_registry_page("Performance Drift Dashboard", "Benchmarks", "performance_drift_dashboard.html", rows, ["drift_type", "metric", "current_seconds", "baseline_seconds", "delta_seconds", "drift_level"], "performance_drift_id", [("Drift entries", len(rows))], benchmark_links(""))}
