"""Deterministically simulate large operational queue scaling."""

from __future__ import annotations

from operator_workflow_common import deterministic_cost, phase39_artifact, risk_level, stable_row_id


def build_queue_scaling_registry(outputs: dict, sizes: list[int] | None = None) -> dict:
    sizes = sizes or [100, 1000, 10000]
    base_queue_count = sum(len((outputs.get(key) or {}).get("queue_items") or []) for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue"])
    validation_count = len((outputs.get("validation_index") or {}).get("validation_entries") or [])
    rows = []
    for size in sizes:
        density = round(size / max(1, base_queue_count or 1), 3)
        rows.append({
            "queue_scaling_id": stable_row_id("QSCALE", size, base_queue_count, validation_count),
            "simulated_queue_items": size,
            "baseline_queue_items": base_queue_count,
            "generation_impact_units": deterministic_cost(size, base=0.0, scale=0.002),
            "dashboard_density_units": deterministic_cost(size, base=0.0, scale=0.0015),
            "validation_impact_units": deterministic_cost(size, validation_count, base=0.0, scale=0.001),
            "rebuild_impact_units": deterministic_cost(size, base=0.0, scale=0.0008),
            "scaling_risk": risk_level(0.2 if size <= 100 else 0.55 if size <= 1000 else 0.9),
            "simulation_deterministic": True,
            "no_runtime_queue_mutation": True,
            "density_multiplier": density,
        })
    artifact = phase39_artifact("deterministic_queue_scaling_simulator_v1")
    artifact.update({"queue_scaling_registry_id": stable_row_id("QSCALEREG", [row["queue_scaling_id"] for row in rows]), "simulations": rows, "summary": {"simulation_count": len(rows), "max_simulated_queue_items": max(sizes)}})
    return artifact
