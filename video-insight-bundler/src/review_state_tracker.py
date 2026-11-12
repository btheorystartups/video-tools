"""Review lifecycle state tracking."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id

REVIEW_STATES = {"unreviewed", "in_review", "reviewed", "followup_required", "escalation_required", "deferred", "accepted_risk_candidate", "externally_reviewed", "resolved", "revisit_later"}


def _state_for(annotation: dict) -> str:
    if annotation.get("escalation_required"):
        return "escalation_required"
    if annotation.get("followup_required"):
        return "followup_required"
    if annotation.get("annotation_type") == "accepted_risk_rationale":
        return "accepted_risk_candidate"
    return "in_review"


def build_review_state_registry(outputs: dict, annotations: dict, followups: dict, escalations: dict) -> dict:
    rows = []
    seen = set()
    for ann in annotations.get("annotations") or []:
        for item_type, related in [("segment", ann.get("related_segment")), ("recommendation", ann.get("related_recommendation")), ("blocker", ann.get("related_blocker")), ("review_journey", ann.get("related_review_journey"))]:
            if not related:
                continue
            key = (item_type, related)
            if key in seen:
                continue
            seen.add(key)
            state_id = deterministic_id("RST", item_type, related)
            rows.append({"state_id": state_id, "item_type": item_type, "item_id": related, "review_state": _state_for(ann), "related_annotations": [ann.get("annotation_id")], "followup_required": ann.get("followup_required"), "escalation_required": ann.get("escalation_required"), "state_explanation": "Explicit deterministic review state derived from annotation scaffolding and governance artifacts."})
    for journey in (outputs.get("review_journey_index") or {}).get("journeys") or []:
        item_id = journey.get("journey_id") or journey.get("title")
        if ("review_journey", item_id) not in seen:
            rows.append({"state_id": deterministic_id("RST", "review_journey", item_id), "item_type": "review_journey", "item_id": item_id, "review_state": "unreviewed", "related_annotations": [], "followup_required": False, "escalation_required": False, "state_explanation": "Journey is available for review and has no local reviewer annotation yet."})
    for esc in escalations.get("escalation_items") or []:
        rows.append({"state_id": deterministic_id("RST", "governance_task", esc.get("escalation_id")), "item_type": "governance_review_task", "item_id": esc.get("escalation_id"), "review_state": "escalation_required", "related_annotations": [], "followup_required": True, "escalation_required": True, "state_explanation": esc.get("escalation_reason")})
    output = review_artifact("deterministic_review_state_registry_v1")
    output.update({"review_state_registry_id": deterministic_id("RSTATE", [(row["item_type"], row["item_id"], row["review_state"]) for row in rows]), "state_items": rows, "allowed_states": sorted(REVIEW_STATES), "summary": {"state_item_count": len(rows), "followup_required_count": sum(1 for row in rows if row["followup_required"]), "escalation_required_count": sum(1 for row in rows if row["escalation_required"])}})
    return output
