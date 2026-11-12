"""Queue integration for reconciliation outcomes."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact
from stability import deterministic_id


def build_reconciliation_queues(conflicts: dict, merge_results: dict, import_registry: dict) -> dict:
    unresolved = [{"queue_id": deterministic_id("RCQ", row.get("conflict_id")), "conflict_id": row.get("conflict_id"), "queue_type": "unresolved_conflict", "severity": row.get("severity"), "governance_relevance": row.get("governance_relevance"), "suggested_next_action": row.get("suggested_manual_review")} for row in conflicts.get("conflicts") or []]
    required = [{"queue_id": deterministic_id("RRQ", row.get("merge_result_id")), "import_item_id": row.get("import_item_id"), "queue_type": "reconciliation_required", "severity": "high" if row.get("reconciliation_outcome") == "conflict_detected" else "medium", "suggested_next_action": "Review import result before operational state is changed."} for row in merge_results.get("merge_results") or [] if row.get("requires_manual_review")]
    followups = [{"queue_id": deterministic_id("IFQ", row.get("import_item_id")), "import_item_id": row.get("import_item_id"), "queue_type": "imported_review_followup", "severity": "medium", "suggested_next_action": "Review imported follow-up and decide whether to create an operational follow-up item."} for row in import_registry.get("imported_items") or [] if row.get("followup_required")]
    return {
        "unresolved_conflict_queue": _queue("unresolved_conflict_queue", unresolved),
        "reconciliation_required_queue": _queue("reconciliation_required_queue", required),
        "imported_review_followup_queue": _queue("imported_review_followup_queue", followups),
    }


def _queue(name: str, rows: list[dict]) -> dict:
    artifact = review_artifact(f"deterministic_{name}_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({f"{name}_id": deterministic_id(name.upper()[:10], [row.get("queue_id") for row in rows]), "queue_items": rows, "summary": {"queue_item_count": len(rows)}})
    return artifact
