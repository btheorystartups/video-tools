"""Audit trail for review import reconciliation actions."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact, stable_timestamp
from stability import deterministic_id


def build_review_merge_audit(merge_results: dict, conflicts: dict, provenance: dict) -> dict:
    rows = []
    for result in merge_results.get("merge_results") or []:
        audit_id = deterministic_id("MAUD", result.get("merge_result_id"))
        rows.append({"audit_id": audit_id, "timestamp": stable_timestamp(audit_id), "action_type": "review_import_reconciliation", "import_item_id": result.get("import_item_id"), "merge_outcome": result.get("reconciliation_outcome"), "operational_state_mutated": False, "audit_note": "Recorded reconciliation outcome without overwriting existing review state."})
    for conflict in conflicts.get("conflicts") or []:
        audit_id = deterministic_id("MAUD", conflict.get("conflict_id"))
        rows.append({"audit_id": audit_id, "timestamp": stable_timestamp(audit_id), "action_type": "conflict_detected", "conflict_id": conflict.get("conflict_id"), "merge_outcome": "requires_manual_review", "operational_state_mutated": False, "audit_note": "Conflict queued for human review; no autonomous resolution performed."})
    artifact = review_artifact("deterministic_review_merge_audit_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"reconciliation_audit_log_id": deterministic_id("MAUDREG", [row["audit_id"] for row in rows]), "audit_events": rows, "summary": {"audit_event_count": len(rows), "operational_state_mutated": False}})
    return artifact
