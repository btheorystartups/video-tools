"""Validation for human review imports before reconciliation."""

from __future__ import annotations

from review_import_templates import ALLOWED_DECISIONS, ALLOWED_ESCALATION_STATES, ALLOWED_REVIEW_STATES, IMPORT_LIMITATION, TEMPLATE_VERSION
from review_operational_common import review_artifact
from stability import deterministic_id


def validate_review_imports(import_registry: dict, outputs: dict) -> dict:
    existing_ids = {row.get("annotation_id") for row in (outputs.get("reviewer_annotations") or {}).get("annotations") or []}
    checkpoint_ids = {row.get("checkpoint_id") for row in (outputs.get("review_checkpoints") or {}).get("checkpoints") or []}
    seen = set()
    valid = []
    invalid = []
    for row in import_registry.get("imported_items") or []:
        errors = []
        item_id = row.get("import_item_id")
        if not item_id:
            errors.append("missing_import_item_id")
        if item_id in seen:
            errors.append("duplicate_import_item_id")
        seen.add(item_id)
        if row.get("source_item_id") and row.get("source_item_id") not in existing_ids:
            errors.append("orphaned_source_item_reference")
        if row.get("review_state") and row.get("review_state") not in ALLOWED_REVIEW_STATES:
            errors.append("invalid_review_state")
        if row.get("decision") and row.get("decision") not in ALLOWED_DECISIONS:
            errors.append("invalid_decision")
        if row.get("escalation_state") and row.get("escalation_state") not in ALLOWED_ESCALATION_STATES:
            errors.append("invalid_escalation_state")
        if row.get("checkpoint_reference") and row.get("checkpoint_reference") not in checkpoint_ids:
            errors.append("incompatible_checkpoint_reference")
        if row.get("template_version") != TEMPLATE_VERSION:
            errors.append("unsupported_template_version")
        if row.get("decision") == "accepted_risk" and row.get("escalation_state") in {"active", "requested"}:
            errors.append("governance_conflict_unresolved_escalation")
        target = invalid if errors else valid
        target.append({"import_item_id": item_id, "source_item_id": row.get("source_item_id"), "validation_status": "rejected_invalid" if errors else "valid", "errors": errors, "import_type": row.get("import_type")})
    artifact = review_artifact("deterministic_review_import_validation_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"review_import_validation_id": deterministic_id("IMPVAL", [row.get("import_item_id") for row in valid], [row.get("import_item_id") for row in invalid]), "valid_imports": valid, "invalid_imports": invalid, "summary": {"valid_import_count": len(valid), "invalid_import_count": len(invalid), "duplicate_import_count": sum(1 for row in invalid if "duplicate_import_item_id" in row.get("errors", [])), "governance_conflict_count": sum(1 for row in invalid if any("governance" in err for err in row.get("errors", [])))}})
    return artifact
