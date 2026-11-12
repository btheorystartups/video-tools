"""Append-preserving reconciliation for imported reviewer content."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact
from stability import deterministic_id


def reconcile_review_imports(import_registry: dict, validation: dict, conflicts: dict, outputs: dict) -> dict:
    invalid_ids = {row.get("import_item_id") for row in validation.get("invalid_imports") or []}
    conflict_item_ids = {item for conflict in conflicts.get("conflicts") or [] for item in conflict.get("conflicting_items") or []}
    seen = set()
    results = []
    existing_ids = {row.get("annotation_id") for row in (outputs.get("reviewer_annotations") or {}).get("annotations") or []}
    for row in import_registry.get("imported_items") or []:
        item_id = row.get("import_item_id")
        if item_id in invalid_ids:
            outcome = "rejected_invalid"
        elif item_id in seen:
            outcome = "duplicate_ignored"
        elif item_id in conflict_item_ids:
            outcome = "conflict_detected"
        elif row.get("source_item_id") in existing_ids:
            outcome = "merged_cleanly"
        else:
            outcome = "appended"
        seen.add(item_id)
        results.append({"merge_result_id": deterministic_id("MRG", item_id, outcome), "import_item_id": item_id, "source_item_id": row.get("source_item_id"), "reconciliation_outcome": outcome, "operational_state_mutated": False, "append_preserving": True, "requires_manual_review": outcome in {"conflict_detected", "rejected_invalid"}})
    artifact = review_artifact("deterministic_review_reconciliation_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"review_import_merge_results_id": deterministic_id("MRGREG", [row["merge_result_id"] for row in results]), "merge_results": results, "summary": _summary(results)})
    return artifact


def build_reconciliation_registry(merge_results: dict, conflicts: dict) -> dict:
    passes = [{"reconciliation_pass_id": deterministic_id("RPASS", merge_results.get("review_import_merge_results_id"), conflicts.get("reconciliation_conflicts_id")), "merge_result_count": len(merge_results.get("merge_results") or []), "conflict_count": len(conflicts.get("conflicts") or []), "operational_state_mutated": False, "manual_review_required": bool(conflicts.get("conflicts"))}]
    artifact = review_artifact("deterministic_reconciliation_registry_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"reconciliation_registry_id": deterministic_id("RREG", [row["reconciliation_pass_id"] for row in passes]), "reconciliation_passes": passes, "summary": {"pass_count": len(passes), "manual_review_required": any(row["manual_review_required"] for row in passes)}})
    return artifact


def build_reconciliation_resolutions(conflicts: dict) -> dict:
    rows = [{"conflict_id": row.get("conflict_id"), "resolution_status": "unresolved", "resolved_by": None, "resolution_note": "No autonomous resolution performed."} for row in conflicts.get("conflicts") or []]
    artifact = review_artifact("deterministic_reconciliation_resolutions_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"reconciliation_resolutions_id": deterministic_id("RRES", [row["conflict_id"] for row in rows]), "resolutions": rows, "summary": {"resolution_count": len(rows), "unresolved_count": len(rows)}})
    return artifact


def build_imported_vs_existing_diff(import_registry: dict, outputs: dict) -> dict:
    existing = {row.get("annotation_id"): row for row in (outputs.get("reviewer_annotations") or {}).get("annotations") or []}
    rows = []
    for row in import_registry.get("imported_items") or []:
        old = existing.get(row.get("source_item_id")) or {}
        rows.append({"diff_id": deterministic_id("RDIFF", row.get("import_item_id"), row.get("source_item_id")), "import_item_id": row.get("import_item_id"), "source_item_id": row.get("source_item_id"), "existing_review_status": old.get("review_status"), "imported_review_state": row.get("review_state"), "existing_escalation_required": old.get("escalation_required"), "imported_escalation_state": row.get("escalation_state"), "change_requires_manual_review": old.get("review_status") != row.get("review_state") or bool(old.get("escalation_required")) != (row.get("escalation_state") != "none")})
    artifact = review_artifact("deterministic_imported_vs_existing_review_diff_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"imported_vs_existing_review_diff_id": deterministic_id("RDIFFREG", [row["diff_id"] for row in rows]), "diffs": rows, "summary": {"diff_count": len(rows), "manual_review_change_count": sum(1 for row in rows if row["change_requires_manual_review"])}})
    return artifact


def _summary(rows: list[dict]) -> dict:
    return {f"{key}_count": sum(1 for row in rows if row["reconciliation_outcome"] == key) for key in ["appended", "merged_cleanly", "conflict_detected", "rejected_invalid", "duplicate_ignored"]} | {"merge_result_count": len(rows)}
