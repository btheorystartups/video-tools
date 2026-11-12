"""Summaries for completed reviewer template re-import."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact
from stability import deterministic_id


def build_reviewer_response_import_summary(import_registry: dict, validation: dict, merge_results: dict, queues: dict) -> dict:
    artifact = review_artifact("deterministic_reviewer_response_import_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"reviewer_response_import_id": deterministic_id("RRIMP", import_registry.get("review_import_registry_id"), validation.get("review_import_validation_id"), merge_results.get("review_import_merge_results_id")), "import_summary": import_registry.get("summary") or {}, "validation_summary": validation.get("summary") or {}, "reconciliation_summary": merge_results.get("summary") or {}, "unresolved_conflict_queue_count": ((queues.get("unresolved_conflict_queue") or {}).get("summary") or {}).get("queue_item_count", 0), "summary": {"completed_template_import_supported": True, "manual_review_required": ((queues.get("unresolved_conflict_queue") or {}).get("summary") or {}).get("queue_item_count", 0) > 0}})
    return artifact
