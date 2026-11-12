"""Side-by-side reviewer disagreement registry."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id


def build_reviewer_disagreement_registry(conflicts: dict, import_registry: dict, rationale_diff_registry: dict, governance_conflict_analysis: dict) -> dict:
    imports = {row.get("import_item_id"): row for row in import_registry.get("imported_items") or []}
    diffs = {row.get("conflict_id"): row for row in rationale_diff_registry.get("rationale_diffs") or []}
    impacts = {row.get("conflict_id"): row for row in governance_conflict_analysis.get("governance_conflicts") or []}
    rows = []
    for conflict in conflicts.get("conflicts") or []:
        items = [imports.get(item_id) or {} for item_id in conflict.get("conflicting_items") or []]
        a = items[0] if items else {}
        b = items[1] if len(items) > 1 else {}
        rows.append(
            {
                "disagreement_id": deterministic_id("DVIEW", conflict.get("conflict_id")),
                "conflict_id": conflict.get("conflict_id"),
                "source_item_id": conflict.get("source_item_id"),
                "reviewer_a_state": _state(a),
                "reviewer_b_state": _state(b),
                "rationale_differences": (diffs.get(conflict.get("conflict_id")) or {}).get("rationale_conflicts") or [],
                "evidence_differences": (diffs.get(conflict.get("conflict_id")) or {}).get("evidence_disagreement") or [],
                "governance_implications": (impacts.get(conflict.get("conflict_id")) or {}).get("governance_impact_summary"),
                "unresolved_ambiguity": (diffs.get(conflict.get("conflict_id")) or {}).get("unresolved_ambiguity") or [],
                "suggested_manual_review": "Reviewer disagreement requires side-by-side human adjudication; no record is preferred automatically.",
            }
        )
    artifact = adjudication_artifact("deterministic_reviewer_disagreement_views_v1")
    artifact.update({"reviewer_disagreement_registry_id": deterministic_id("DVIEWREG", [row["disagreement_id"] for row in rows]), "disagreements": rows, "summary": {"disagreement_count": len(rows)}})
    return artifact


def _state(item: dict) -> dict:
    return {
        "import_item_id": item.get("import_item_id"),
        "reviewer_id": item.get("reviewer_id"),
        "decision": item.get("decision"),
        "review_state": item.get("review_state"),
        "escalation_state": item.get("escalation_state"),
        "rationale": item.get("rationale_text") or item.get("reviewer_notes"),
        "evidence_refs": item.get("evidence_refs") or [],
    }
