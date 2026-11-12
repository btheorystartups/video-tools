"""Deterministic validation timing summaries."""

from __future__ import annotations

from operator_workflow_common import deterministic_cost, phase39_artifact, stable_row_id


def build_validation_timing_registry(outputs: dict) -> dict:
    validations = (outputs.get("validation_index") or {}).get("validation_entries") or []
    rows = []
    for row in validations:
        deps = len(row.get("dependencies") or [])
        rows.append({
            "validation_timing_id": stable_row_id("VTIME", row.get("artifact"), row.get("cache_key")),
            "artifact": row.get("artifact"),
            "validation_scope": row.get("validation_scope"),
            "estimated_validation_seconds": deterministic_cost(deps, len(str(row.get("cache_key") or "")), base=0.02, scale=0.001),
            "cache_reusable": row.get("cache_reusable", False),
            "timing_source": "deterministic_complexity_estimate",
        })
    artifact = phase39_artifact("deterministic_validation_timing_profiler_v1")
    artifact.update({"validation_timing_registry_id": stable_row_id("VTIMEREG", [row["validation_timing_id"] for row in rows]), "timing_entries": rows, "summary": {"timing_entry_count": len(rows), "estimated_total_validation_seconds": round(sum(row["estimated_validation_seconds"] for row in rows), 3)}})
    return artifact
