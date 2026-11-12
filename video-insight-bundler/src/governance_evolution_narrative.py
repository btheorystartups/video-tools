"""Deterministic governance evolution narratives."""

from __future__ import annotations

from phase42_narrative_common import base_registry_id, governance_rows, phase42_artifact, render_narrative_page, stable_row_id


def build_governance_evolution_narrative(outputs: dict) -> dict:
    rows = []
    for index, row in enumerate(governance_rows(outputs)):
        rows.append(
            {
                "governance_evolution_id": stable_row_id("GEV", index, row.get("governance_drift_id")),
                "evolution_type": row.get("drift_type"),
                "current_count": row.get("current_count", 0),
                "pressure_score": row.get("pressure_score", 0),
                "narrative": f"Governance {row.get('drift_type')} is tracked at {row.get('current_count', 0)} with pressure score {row.get('pressure_score', 0)}.",
                "human_review_required": True,
            }
        )
    artifact = phase42_artifact("deterministic_governance_evolution_narrative_v1")
    artifact.update({"governance_evolution_narrative_id": base_registry_id("GEVREG", rows, "governance_evolution_id"), "governance_evolution_entries": rows, "summary": {"governance_evolution_count": len(rows)}})
    return artifact


def render_governance_evolution_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("governance_evolution_narrative") or {}).get("governance_evolution_entries") or []
    return render_narrative_page("Governance Evolution Dashboard", "governance_evolution_dashboard.html", rows, ["evolution_type", "current_count", "pressure_score", "narrative"], "governance_evolution_id", [("Governance entries", len(rows))])
