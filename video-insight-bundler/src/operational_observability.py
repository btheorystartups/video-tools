"""Combine Phase 39 signals into an operational observability registry."""

from __future__ import annotations

from operator_workflow_common import phase39_artifact, stable_row_id


def build_operational_observability_registry(outputs: dict) -> dict:
    specs = [
        ("import_previews", (outputs.get("import_preview_registry") or {}).get("summary", {}).get("preview_count") or 0, "operator import review"),
        ("validation_timing", (outputs.get("validation_timing_registry") or {}).get("summary", {}).get("estimated_total_validation_seconds") or 0, "validation planning"),
        ("rebuild_cost", (outputs.get("rebuild_cost_registry") or {}).get("summary", {}).get("estimated_total_cost_units") or 0, "selective regeneration"),
        ("queue_scaling", (outputs.get("queue_scaling_registry") or {}).get("summary", {}).get("max_simulated_queue_items") or 0, "large queue planning"),
        ("throughput", (outputs.get("throughput_analysis_registry") or {}).get("summary", {}).get("estimated_total_operator_hours") or 0, "operator workload planning"),
        ("scalability_warnings", (outputs.get("scalability_warning_registry") or {}).get("summary", {}).get("warning_count") or 0, "scalability review"),
    ]
    rows = []
    for signal, value, relevance in specs:
        rows.append({
            "observability_id": stable_row_id("OBS", signal, value),
            "signal": signal,
            "value": value,
            "status": "visible",
            "operator_relevance": relevance,
            "deterministic_signal": True,
        })
    artifact = phase39_artifact("deterministic_operational_observability_v1")
    artifact.update({"operational_observability_registry_id": stable_row_id("OBSREG", [row["observability_id"] for row in rows]), "observability_entries": rows, "summary": {"signal_count": len(rows)}})
    return artifact
