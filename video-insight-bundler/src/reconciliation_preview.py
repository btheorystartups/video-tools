"""Preview likely reconciliation outcomes before import."""

from __future__ import annotations

from operator_workflow_common import phase39_artifact, risk_level, stable_row_id


def build_reconciliation_preview_registry(outputs: dict) -> dict:
    imports = (outputs.get("review_import_registry") or {}).get("imported_items") or []
    conflicts = (outputs.get("reconciliation_conflicts") or {}).get("conflicts") or []
    conflict_sources = {item for row in conflicts for item in (row.get("conflicting_items") or [])}
    rows = []
    seen_sources = set()
    for item in imports:
        duplicate = item.get("source_item_id") in seen_sources
        seen_sources.add(item.get("source_item_id"))
        governance = item.get("escalation_state") not in {None, "", "none"} or "governance" in str(item.get("reviewer_notes", "")).lower()
        conflict = item.get("import_item_id") in conflict_sources or duplicate
        if governance:
            outcome = "governance_review_required"
        elif conflict:
            outcome = "likely_conflict"
        elif duplicate:
            outcome = "duplicate_likely"
        else:
            outcome = "likely_append"
        rows.append({
            "reconciliation_preview_id": stable_row_id("RPREV", item.get("import_item_id"), outcome),
            "import_item_id": item.get("import_item_id"),
            "source_item_id": item.get("source_item_id"),
            "expected_outcome": outcome,
            "conflict_likelihood": risk_level(0.8 if conflict else 0.25),
            "governance_review_required": governance,
            "escalation_likely": governance and item.get("escalation_state") == "requested",
            "duplicate_likely": duplicate,
            "autonomous_resolution_performed": False,
        })
    artifact = phase39_artifact("deterministic_reconciliation_preview_v1")
    artifact.update({
        "reconciliation_preview_registry_id": stable_row_id("RPREVREG", [row["reconciliation_preview_id"] for row in rows]),
        "previews": rows,
        "summary": {
            "preview_count": len(rows),
            "likely_conflict_count": sum(1 for row in rows if row["expected_outcome"] == "likely_conflict"),
            "governance_review_required_count": sum(1 for row in rows if row["governance_review_required"]),
        },
    })
    return artifact
