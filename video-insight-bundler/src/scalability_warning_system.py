"""Deterministic informational scalability warnings."""

from __future__ import annotations

from operator_workflow_common import phase39_artifact, risk_level, stable_row_id


def build_scalability_warning_registry(outputs: dict) -> dict:
    queue_max = max([row.get("simulated_queue_items") or 0 for row in (outputs.get("queue_scaling_registry") or {}).get("simulations") or []] or [0])
    validation_seconds = (outputs.get("validation_timing_registry") or {}).get("summary", {}).get("estimated_total_validation_seconds") or 0
    max_depth = (outputs.get("rebuild_cost_registry") or {}).get("summary", {}).get("max_dependency_chain_depth") or 0
    dashboard_count = (outputs.get("dashboard_render_registry") or {}).get("summary", {}).get("dashboard_count") or 0
    artifact_count = (outputs.get("artifact_density_registry") or {}).get("summary", {}).get("artifact_count") or 0
    specs = [
        ("queue_overload_risk", queue_max, 10000, "Review queue filtering and pagination should be inspected."),
        ("validation_slowdown_risk", validation_seconds, 1.0, "Review validation cache and schema scope before reruns."),
        ("dependency_chain_depth_risk", max_depth, 4, "Inspect dependency-aware regeneration scope."),
        ("dashboard_density_overload", dashboard_count, 12, "Inspect dashboard grouping and operator navigation."),
        ("artifact_explosion_risk", artifact_count, 30, "Inspect artifact index density before adding more registries."),
    ]
    rows = []
    for warning_type, value, threshold, action in specs:
        score = min(1.0, float(value) / float(threshold or 1))
        rows.append({
            "scalability_warning_id": stable_row_id("SCALEWARN", warning_type, value, threshold),
            "warning_type": warning_type,
            "evidence_count": value,
            "threshold": threshold,
            "risk_level": risk_level(score),
            "operator_action": action,
            "informational_only": True,
            "autonomous_action_taken": False,
        })
    artifact = phase39_artifact("deterministic_scalability_warning_system_v1")
    artifact.update({"scalability_warning_registry_id": stable_row_id("SCALEWARNREG", [row["scalability_warning_id"] for row in rows]), "warnings": rows, "summary": {"warning_count": len(rows), "high_warning_count": sum(1 for row in rows if row["risk_level"] == "high")}})
    return artifact
