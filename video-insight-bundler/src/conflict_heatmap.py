"""Conflict heatmap data for adjudication dashboards."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id


def build_conflict_heatmap(governance_conflict_analysis: dict, unresolved_ambiguity_registry: dict, reviewer_disagreement_registry: dict, adjudication_queue_registry: dict) -> dict:
    ambiguity = {row.get("conflict_id"): row for row in unresolved_ambiguity_registry.get("ambiguities") or []}
    disagreements = {row.get("conflict_id"): row for row in reviewer_disagreement_registry.get("disagreements") or []}
    queues = {row.get("conflict_id"): row for row in adjudication_queue_registry.get("queue_items") or []}
    rows = []
    for impact in governance_conflict_analysis.get("governance_conflicts") or []:
        conflict_id = impact.get("conflict_id")
        queue_types = (queues.get(conflict_id) or {}).get("queue_types") or []
        rows.append(
            {
                "heatmap_cell_id": deterministic_id("CHM", conflict_id),
                "conflict_id": conflict_id,
                "governance_severity": impact.get("governance_severity"),
                "unresolved_ambiguity": len((ambiguity.get(conflict_id) or {}).get("ambiguity_types") or []),
                "reviewer_disagreement_count": 1 if conflict_id in disagreements else 0,
                "escalation_density": 1 if "arbitration required" in queue_types or "governance critical" in queue_types else 0,
                "unresolved_followups": len(queue_types),
                "heatmap_intensity": min(1.0, round((len(queue_types) * 0.15) + (0.1 * len((ambiguity.get(conflict_id) or {}).get("ambiguity_types") or [])), 3)),
            }
        )
    artifact = adjudication_artifact("deterministic_conflict_heatmap_v1")
    artifact.update({"conflict_heatmap_id": deterministic_id("CHMREG", [row["heatmap_cell_id"] for row in rows]), "heatmap_cells": rows, "summary": {"heatmap_cell_count": len(rows)}})
    return artifact
