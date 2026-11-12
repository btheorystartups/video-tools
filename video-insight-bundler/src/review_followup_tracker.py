"""Follow-up item tracking for operational review continuity."""

from __future__ import annotations

from review_operational_common import review_artifact, stable_timestamp
from stability import deterministic_id


def build_review_followup_registry(annotations: dict, escalations: dict) -> dict:
    items = []
    for row in annotations.get("annotations") or []:
        if not row.get("followup_required"):
            continue
        followup_id = deterministic_id("FUP", row.get("annotation_id"))
        items.append(
            {
                "followup_id": followup_id,
                "followup_type": "governance revisit" if row.get("related_blocker") else "re-review after edit" if row.get("related_recommendation") else "unresolved ambiguity",
                "related_annotation": row.get("annotation_id"),
                "related_item": row.get("related_recommendation") or row.get("related_blocker") or row.get("related_segment"),
                "severity": row.get("severity") or "review",
                "status": "open",
                "required_action": "Record reviewer decision, rationale, or deferral outcome.",
                "evidence_refs": row.get("evidence_refs") or [],
                "timestamp": stable_timestamp(followup_id),
            }
        )
    for esc in escalations.get("escalation_items") or []:
        followup_id = deterministic_id("FUP", esc.get("escalation_id"))
        items.append({"followup_id": followup_id, "followup_type": "escalation follow-up", "related_annotation": None, "related_item": esc.get("escalation_id"), "severity": esc.get("severity"), "status": "open", "required_action": esc.get("suggested_reviewer_action"), "evidence_refs": esc.get("evidence_refs") or [], "timestamp": stable_timestamp(followup_id)})
    output = review_artifact("deterministic_review_followup_registry_v1")
    output.update({"review_followup_registry_id": deterministic_id("FUPREG", [row["followup_id"] for row in items]), "followup_items": items, "summary": {"followup_count": len(items), "open_followup_count": sum(1 for row in items if row["status"] == "open")}})
    return output
