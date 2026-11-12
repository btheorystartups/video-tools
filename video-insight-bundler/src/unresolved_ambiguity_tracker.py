"""Explicit unresolved ambiguity tracking for adjudication."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id


def build_unresolved_ambiguity_registry(conflicts: dict, rationale_diff_registry: dict, governance_conflict_analysis: dict) -> dict:
    impacts = {row.get("conflict_id"): row for row in governance_conflict_analysis.get("governance_conflicts") or []}
    rows = []
    for diff in rationale_diff_registry.get("rationale_diffs") or []:
        ambiguity_types = list(diff.get("unresolved_ambiguity") or [])
        impact = impacts.get(diff.get("conflict_id")) or {}
        if impact.get("requires_arbitration"):
            ambiguity_types.append("unresolved escalation")
        if not ambiguity_types:
            ambiguity_types.append("reviewer disagreement")
        rows.append(
            {
                "ambiguity_id": deterministic_id("AMB", diff.get("conflict_id"), ambiguity_types),
                "conflict_id": diff.get("conflict_id"),
                "source_item_id": diff.get("source_item_id"),
                "ambiguity_types": sorted(set(ambiguity_types)),
                "ambiguity_status": "unresolved",
                "manual_clarification_required": True,
                "governance_sensitive": bool(impact.get("requires_governance_reviewer")),
                "suggested_manual_question": "What evidence and rationale should govern this conflict disposition?",
            }
        )
    artifact = adjudication_artifact("deterministic_unresolved_ambiguity_tracker_v1")
    artifact.update({"unresolved_ambiguity_registry_id": deterministic_id("AMBREG", [row["ambiguity_id"] for row in rows]), "ambiguities": rows, "summary": {"ambiguity_count": len(rows), "unresolved_count": len(rows)}})
    return artifact
