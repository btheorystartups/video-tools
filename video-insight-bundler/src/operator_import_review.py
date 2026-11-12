"""Operator import review registry."""

from __future__ import annotations

from operator_workflow_common import phase39_artifact, stable_row_id


def build_operator_import_review_registry(import_preview: dict, validation_preview: dict, reconciliation_preview: dict) -> dict:
    validation_by_import = {row.get("import_item_id"): row for row in validation_preview.get("previews") or []}
    reconciliation_by_import = {row.get("import_item_id"): row for row in reconciliation_preview.get("previews") or []}
    rows = []
    for preview in import_preview.get("previews") or []:
        import_id = preview.get("import_item_id")
        validation = validation_by_import.get(import_id) or {}
        reconciliation = reconciliation_by_import.get(import_id) or {}
        reasons = []
        if validation.get("requires_operator_review"):
            reasons.append("validation_warning")
        if reconciliation.get("governance_review_required"):
            reasons.append("governance_review_required")
        if reconciliation.get("duplicate_likely"):
            reasons.append("duplicate_likely")
        action = "review_before_import" if reasons else "monitor"
        rows.append({
            "operator_import_review_id": stable_row_id("OPIMP", import_id, reasons),
            "import_item_id": import_id,
            "operator_action": action,
            "review_reason": reasons or ["no_preview_blocker"],
            "governance_visible": bool(preview.get("governance_sensitive") or reconciliation.get("governance_review_required")),
            "validation_state": validation.get("validation_state"),
            "expected_reconciliation_outcome": reconciliation.get("expected_outcome"),
            "preview_only_no_mutation": True,
            "autonomous_decision_made": False,
        })
    artifact = phase39_artifact("deterministic_operator_import_review_v1")
    artifact.update({"operator_import_review_registry_id": stable_row_id("OPIMPR", [row["operator_import_review_id"] for row in rows]), "review_items": rows, "summary": {"review_item_count": len(rows), "manual_review_count": sum(1 for row in rows if row["operator_action"] != "monitor")}})
    return artifact
