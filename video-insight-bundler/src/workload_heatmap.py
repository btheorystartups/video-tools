"""Build operational workload density heatmaps."""

from __future__ import annotations

from operator_workflow_common import clamp, phase39_artifact, risk_level, stable_row_id


def build_workload_heatmap_registry(outputs: dict) -> dict:
    dimensions = [
        ("queue_density", _queue_count(outputs)),
        ("unresolved_ambiguity_density", len((outputs.get("unresolved_ambiguity_registry") or {}).get("ambiguities") or [])),
        ("adjudication_density", len((outputs.get("adjudication_event_registry") or {}).get("events") or [])),
        ("escalation_density", len((outputs.get("governance_escalation_events") or {}).get("escalation_events") or [])),
        ("review_backlog_density", len((outputs.get("review_queue_registry") or {}).get("queue_items") or [])),
        ("validation_density", len((outputs.get("validation_index") or {}).get("validation_entries") or [])),
    ]
    max_count = max([count for _, count in dimensions] or [1], default=1)
    rows = []
    for dimension, count in dimensions:
        score = clamp(count / max(1, max_count))
        rows.append({
            "workload_heatmap_id": stable_row_id("WHEAT", dimension, count),
            "dimension": dimension,
            "density_count": count,
            "density_score": score,
            "density_class": risk_level(score),
            "operator_review_visible": True,
        })
    artifact = phase39_artifact("deterministic_workload_heatmap_v1")
    artifact.update({"workload_heatmap_registry_id": stable_row_id("WHEATREG", [row["workload_heatmap_id"] for row in rows]), "heatmap_cells": rows, "summary": {"dimension_count": len(rows), "max_density_count": max_count}})
    return artifact


def _queue_count(outputs: dict) -> int:
    return sum(len((outputs.get(key) or {}).get("queue_items") or []) for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue", "governance_adjudication_queue"])
