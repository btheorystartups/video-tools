"""Longitudinal workload evolution analysis."""

from __future__ import annotations

from phase41_longitudinal_common import ambiguity_count, count_rows, escalation_count, phase41_artifact, queue_count, render_longitudinal_page, risk_level, stable_row_id


def build_workload_evolution(outputs: dict) -> dict:
    specs = [
        ("queue_density_growth", queue_count(outputs)),
        ("review_backlog_evolution", count_rows(outputs, "review_queue_registry", "queue_items")),
        ("escalation_workload_growth", escalation_count(outputs)),
        ("ambiguity_clustering_growth", ambiguity_count(outputs)),
        ("reviewer_throughput_shift", count_rows(outputs, "throughput_analysis_registry", "throughput_entries")),
    ]
    max_value = max([value for _, value in specs] or [1], default=1)
    rows = [{"workload_evolution_id": stable_row_id("WEVO", kind, value), "evolution_type": kind, "current_count": value, "workload_score": round(value / max(1, max_value), 3), "workload_level": risk_level(value / max(1, max_value)), "human_review_required": True} for kind, value in specs]
    artifact = phase41_artifact("deterministic_workload_evolution_v1")
    artifact.update({"workload_evolution_id": stable_row_id("WEVOREG", [row["workload_evolution_id"] for row in rows]), "workload_evolution_entries": rows, "summary": {"workload_evolution_entry_count": len(rows)}})
    return artifact


def render_workload_evolution_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("workload_evolution") or {}).get("workload_evolution_entries") or []
    return render_longitudinal_page("Workload Evolution Dashboard", "workload_evolution_dashboard.html", rows, ["evolution_type", "current_count", "workload_score", "workload_level"], "workload_evolution_id", [("Workload entries", len(rows))])

