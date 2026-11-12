"""Deterministic human-authored review import normalization."""

from __future__ import annotations

from review_import_templates import IMPORT_LIMITATION, TEMPLATE_VERSION
from review_operational_common import review_artifact, stable_timestamp
from stability import canonical_json, deterministic_id, sha256_text


def _sample_imports(outputs: dict) -> list[dict]:
    annotations = (outputs.get("reviewer_annotations") or {}).get("annotations") or []
    checkpoints = (outputs.get("review_checkpoints") or {}).get("checkpoints") or []
    checkpoint_id = (checkpoints[0] or {}).get("checkpoint_id") if checkpoints else None
    rows = []
    for idx, row in enumerate(annotations[:6]):
        item_type = "decision" if idx % 3 == 1 else "followup" if idx % 3 == 2 else "annotation"
        decision = "accepted_risk" if item_type == "decision" and row.get("escalation_required") else "defer" if item_type == "decision" else None
        import_id = deterministic_id("IMPITEM", row.get("annotation_id"), item_type, idx)
        rows.append({
            "import_item_id": import_id,
            "import_type": item_type,
            "reviewer_id": "local_reviewer_placeholder",
            "source_item_id": row.get("annotation_id"),
            "related_video": row.get("related_video"),
            "related_segment": row.get("related_segment"),
            "related_recommendation": row.get("related_recommendation"),
            "related_blocker": row.get("related_blocker"),
            "review_state": "requires_manual_review" if row.get("escalation_required") else "reviewed",
            "decision": decision,
            "reviewer_notes": f"Imported reviewer response for {row.get('annotation_type')}.",
            "rationale_text": "Human-authored rationale placeholder imported from deterministic local worksheet.",
            "followup_required": bool(row.get("followup_required")),
            "escalation_state": "requested" if row.get("escalation_required") else "none",
            "checkpoint_reference": checkpoint_id,
            "template_version": TEMPLATE_VERSION,
        })
    if annotations:
        duplicate = dict(rows[0])
        duplicate["import_item_id"] = rows[0]["import_item_id"]
        duplicate["reviewer_notes"] = "Duplicate reviewer import used to exercise duplicate handling."
        rows.append(duplicate)
    if len(annotations) > 1:
        conflict = dict(rows[1])
        conflict["import_item_id"] = deterministic_id("IMPITEM", rows[1]["source_item_id"], "conflict")
        conflict["decision"] = "reject" if rows[1].get("decision") != "reject" else "accept"
        conflict["reviewer_notes"] = "Conflicting reviewer decision requiring manual reconciliation."
        rows.append(conflict)
    if annotations:
        invalid = dict(rows[0])
        invalid["import_item_id"] = deterministic_id("IMPITEM", "invalid_escalation", rows[0]["source_item_id"])
        invalid["escalation_state"] = "auto_resolved"
        invalid["reviewer_notes"] = "Invalid escalation state fixture."
        rows.append(invalid)
    return rows


def build_human_review_imports(outputs: dict) -> dict:
    rows = _sample_imports(outputs)
    batch_id = deterministic_id("IMPBATCH", [row.get("import_item_id") for row in rows])
    for row in rows:
        row["import_batch_id"] = batch_id
        row["import_timestamp"] = stable_timestamp(row["import_item_id"])
        row["canonical_hash"] = sha256_text(canonical_json({k: v for k, v in row.items() if k != "canonical_hash"}))
        row["non_claim_limitation"] = IMPORT_LIMITATION
    annotations = [row for row in rows if row.get("import_type") == "annotation"]
    decisions = [row for row in rows if row.get("import_type") == "decision"]
    followups = [row for row in rows if row.get("import_type") == "followup"]
    rationale = [row for row in rows if row.get("rationale_text")]
    registry = review_artifact("deterministic_human_review_import_registry_v1")
    registry["limitations"] = [IMPORT_LIMITATION]
    registry.update({"review_import_registry_id": deterministic_id("IMPREG", batch_id), "import_batches": [{"import_batch_id": batch_id, "template_version": TEMPLATE_VERSION, "imported_item_count": len(rows), "source_format": "deterministic_local_template_fixture", "append_only": True}], "imported_items": rows, "summary": {"imported_item_count": len(rows), "annotation_count": len(annotations), "decision_count": len(decisions), "followup_count": len(followups)}})
    return {"review_import_registry": registry, "imported_reviewer_annotations": _artifact("imported_reviewer_annotations", annotations), "imported_reviewer_decisions": _artifact("imported_reviewer_decisions", decisions), "imported_followups": _artifact("imported_followups", followups), "imported_rationale": _artifact("imported_rationale", rationale)}


def _artifact(name: str, rows: list[dict]) -> dict:
    artifact = review_artifact(f"deterministic_{name}_v1")
    artifact["limitations"] = [IMPORT_LIMITATION]
    artifact.update({f"{name}_id": deterministic_id(name.upper()[:10], [row.get("import_item_id") for row in rows]), "items": rows, "summary": {"item_count": len(rows)}})
    return artifact
