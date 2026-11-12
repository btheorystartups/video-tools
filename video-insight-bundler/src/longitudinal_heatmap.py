"""Longitudinal operational heatmap cells."""

from __future__ import annotations

from phase41_longitudinal_common import ambiguity_count, escalation_count, governance_pressure, phase41_artifact, queue_count, render_longitudinal_page, risk_level, stable_row_id


def build_longitudinal_heatmap(outputs: dict) -> dict:
    lineage = ((outputs.get("persistent_benchmark_lineage") or {}).get("lineage_entries") or [{}])[-1]
    specs = [
        ("governance_pressure", governance_pressure(outputs)),
        ("ambiguity_growth", ambiguity_count(outputs)),
        ("escalation_density", escalation_count(outputs)),
        ("queue_overload", queue_count(outputs)),
        ("validation_cost_growth", float(lineage.get("validation_timing_seconds") or 0)),
        ("rebuild_pressure", float(lineage.get("rebuild_timing_seconds") or 0)),
    ]
    max_value = max([float(value) for _, value in specs] or [1], default=1)
    rows = [{"longitudinal_heatmap_id": stable_row_id("LHEAT", dimension, value), "dimension": dimension, "current_value": value, "heat_score": round(float(value) / max(1.0, max_value), 3), "heat_level": risk_level(float(value) / max(1.0, max_value)), "human_review_required": True} for dimension, value in specs]
    artifact = phase41_artifact("deterministic_longitudinal_heatmap_v1")
    artifact.update({"longitudinal_heatmap_id": stable_row_id("LHEATREG", [row["longitudinal_heatmap_id"] for row in rows]), "heatmap_cells": rows, "summary": {"heatmap_cell_count": len(rows)}})
    return artifact


def render_longitudinal_heatmap_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("longitudinal_heatmap") or {}).get("heatmap_cells") or []
    return render_longitudinal_page("Longitudinal Heatmap Dashboard", "longitudinal_heatmap_dashboard.html", rows, ["dimension", "current_value", "heat_score", "heat_level"], "longitudinal_heatmap_id", [("Heatmap cells", len(rows))])

