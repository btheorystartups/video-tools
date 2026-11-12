"""Detect import reconciliation conflicts without resolving them."""

from __future__ import annotations

from collections import defaultdict

from review_import_templates import IMPORT_LIMITATION
from review_operational_common import review_artifact
from stability import deterministic_id


def detect_review_conflicts(import_registry: dict, validation: dict, outputs: dict) -> dict:
    invalid_ids = {row.get("import_item_id") for row in validation.get("invalid_imports") or []}
    rows = [row for row in import_registry.get("imported_items") or [] if row.get("import_item_id") not in invalid_ids]
    by_source = defaultdict(list)
    for row in rows:
        by_source[row.get("source_item_id")].append(row)
    conflicts = []
    for source, items in sorted(by_source.items()):
        decisions = {row.get("decision") for row in items if row.get("decision")}
        escalation_states = {row.get("escalation_state") for row in items if row.get("escalation_state")}
        if len(decisions) > 1:
            conflicts.append(_conflict("conflicting_reviewer_decisions", source, items, "high", True))
        if "requested" in escalation_states and "resolved_by_human" in escalation_states:
            conflicts.append(_conflict("conflicting_escalation_states", source, items, "high", True))
        notes = {row.get("rationale_text") for row in items if row.get("rationale_text")}
        if len(notes) > 1 and any(row.get("decision") for row in items):
            conflicts.append(_conflict("conflicting_rationale", source, items, "medium", False))
    artifact = review_artifact("deterministic_review_conflict_detection_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({"reconciliation_conflicts_id": deterministic_id("RECONF", [row["conflict_id"] for row in conflicts]), "conflicts": conflicts, "summary": {"conflict_count": len(conflicts), "governance_relevant_count": sum(1 for row in conflicts if row["governance_relevance"])}})
    return artifact


def _conflict(conflict_type: str, source: str | None, items: list[dict], severity: str, governance: bool) -> dict:
    item_ids = [row.get("import_item_id") for row in items]
    return {"conflict_id": deterministic_id("RCF", conflict_type, source, item_ids), "conflicting_items": item_ids, "source_item_id": source, "conflict_type": conflict_type, "severity": severity, "governance_relevance": governance, "suggested_manual_review": "Compare imported reviewer response against existing review state before any operational state change.", "unresolved_status": "unresolved"}
