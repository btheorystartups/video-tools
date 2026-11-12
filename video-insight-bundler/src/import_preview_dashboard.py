"""Build operator-facing import and validation preview registries."""

from __future__ import annotations

from operator_workflow_common import operator_links, phase39_artifact, render_registry_page, risk_level, stable_row_id


def build_import_preview_registry(outputs: dict, markdown_ingestion: dict | None = None) -> dict:
    imports = (outputs.get("review_import_registry") or {}).get("imported_items") or []
    validation = outputs.get("review_import_validation") or {}
    invalid = {row.get("import_item_id") for row in validation.get("invalid_imports") or []}
    duplicates = {row.get("import_item_id") for row in validation.get("duplicate_imports") or []}
    queue_refs = _queue_refs(outputs)
    rows = []
    for item in imports:
        governance = item.get("escalation_state") not in {None, "", "none"} or "governance" in str(item.get("reviewer_notes", "")).lower()
        warnings = []
        if item.get("import_item_id") in invalid:
            warnings.append("invalid_import")
        if item.get("import_item_id") in duplicates:
            warnings.append("duplicate_import")
        if governance:
            warnings.append("governance_sensitive")
        rows.append({
            "import_preview_id": stable_row_id("IPREV", item.get("import_item_id"), warnings),
            "import_item_id": item.get("import_item_id"),
            "import_type": item.get("import_type"),
            "source_item_id": item.get("source_item_id"),
            "imported_decision": item.get("decision"),
            "imported_rationale": item.get("rationale_text"),
            "validation_warnings": warnings,
            "conflict_likelihood": risk_level(0.75 if warnings else 0.25),
            "governance_sensitive": governance,
            "affected_operational_queues": queue_refs,
            "preview_only_no_mutation": True,
        })
    artifact = phase39_artifact("deterministic_import_preview_registry_v1")
    artifact.update({
        "import_preview_registry_id": stable_row_id("IPREVREG", [row["import_preview_id"] for row in rows]),
        "previews": rows,
        "markdown_candidate_count": len((markdown_ingestion or {}).get("import_candidates") or []),
        "summary": {"preview_count": len(rows), "warning_count": sum(len(row["validation_warnings"]) for row in rows), "governance_sensitive_count": sum(1 for row in rows if row["governance_sensitive"])},
    })
    return artifact


def build_validation_preview_registry(outputs: dict, import_preview: dict) -> dict:
    rows = []
    for preview in import_preview.get("previews") or []:
        warnings = preview.get("validation_warnings") or []
        rows.append({
            "validation_preview_id": stable_row_id("VPREV", preview.get("import_preview_id"), warnings),
            "import_item_id": preview.get("import_item_id"),
            "validation_state": "blocked_for_manual_review" if "invalid_import" in warnings else "warnings_present" if warnings else "ready_for_reconciliation_preview",
            "warning_count": len(warnings),
            "warnings": warnings,
            "requires_operator_review": bool(warnings),
            "preview_only_no_mutation": True,
        })
    artifact = phase39_artifact("deterministic_validation_preview_registry_v1")
    artifact.update({"validation_preview_registry_id": stable_row_id("VPREVREG", [row["validation_preview_id"] for row in rows]), "previews": rows, "summary": {"preview_count": len(rows), "requires_operator_review_count": sum(1 for row in rows if row["requires_operator_review"])}})
    return artifact


def render_import_preview_dashboards(outputs: dict) -> dict[str, str]:
    import_rows = (outputs.get("import_preview_registry") or {}).get("previews") or []
    validation_rows = (outputs.get("validation_preview_registry") or {}).get("previews") or []
    reconciliation_rows = (outputs.get("reconciliation_preview_registry") or {}).get("previews") or []
    review_rows = (outputs.get("operator_import_review_registry") or {}).get("review_items") or []
    links = operator_links("")
    return {
        "import_preview_dashboard.html": render_registry_page("Import Preview Dashboard", "Operator Import", "import_preview_dashboard.html", import_rows, ["import_type", "source_item_id", "validation_warnings", "conflict_likelihood", "governance_sensitive"], "import_preview_id", [("Import previews", len(import_rows)), ("Governance sensitive", sum(1 for row in import_rows if row.get("governance_sensitive")))], links),
        "validation_preview_dashboard.html": render_registry_page("Validation Preview Dashboard", "Operator Import", "validation_preview_dashboard.html", validation_rows, ["import_item_id", "validation_state", "warning_count", "requires_operator_review"], "validation_preview_id", [("Validation previews", len(validation_rows)), ("Needs review", sum(1 for row in validation_rows if row.get("requires_operator_review")))], links),
        "reconciliation_preview_dashboard.html": render_registry_page("Reconciliation Preview Dashboard", "Operator Import", "reconciliation_preview_dashboard.html", reconciliation_rows, ["source_item_id", "expected_outcome", "conflict_likelihood", "governance_review_required", "duplicate_likely"], "reconciliation_preview_id", [("Reconciliation previews", len(reconciliation_rows)), ("Governance review", sum(1 for row in reconciliation_rows if row.get("governance_review_required")))], links),
        "operator_import_dashboard.html": render_registry_page("Operator Import Review Dashboard", "Operator Import", "operator_import_dashboard.html", review_rows, ["import_item_id", "operator_action", "review_reason", "governance_visible", "preview_only_no_mutation"], "operator_import_review_id", [("Operator review items", len(review_rows)), ("Manual actions", sum(1 for row in review_rows if row.get("operator_action") != "monitor"))], links),
    }


def _queue_refs(outputs: dict) -> list[str]:
    refs = []
    for key in ["unresolved_conflict_queue", "reconciliation_required_queue", "imported_review_followup_queue", "governance_adjudication_queue"]:
        if outputs.get(key):
            refs.append(f"queues/{key}.json")
    return refs
