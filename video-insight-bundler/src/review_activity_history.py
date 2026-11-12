"""Deterministic review activity history."""

from __future__ import annotations

from review_operational_common import review_artifact, stable_timestamp
from stability import deterministic_id


def build_review_activity_history(annotations: dict, checkpoints: dict, queues: dict, followups: dict, escalations: dict, rationales: dict) -> dict:
    events = []
    for source, action, rows, key in [
        ("annotations/reviewer_annotations.json", "annotation_available", annotations.get("annotations") or [], "annotation_id"),
        ("review_sessions/review_checkpoints.json", "checkpoint_available", checkpoints.get("checkpoints") or [], "checkpoint_id"),
        ("queues/review_queue_registry.json", "queue_item_available", queues.get("queue_items") or [], "queue_id"),
        ("review_sessions/review_followup_registry.json", "followup_opened", followups.get("followup_items") or [], "followup_id"),
        ("review_sessions/review_escalation_registry.json", "escalation_opened", escalations.get("escalation_items") or [], "escalation_id"),
        ("review_sessions/reviewer_rationale_registry.json", "rationale_available", rationales.get("rationales") or [], "rationale_id"),
    ]:
        for row in rows:
            event_id = deterministic_id("RACT", action, row.get(key))
            events.append({"activity_id": event_id, "activity_type": action, "related_item": row.get(key), "source_artifact": source, "timestamp": stable_timestamp(event_id), "audit_note": "Append-preserving deterministic activity entry; no media or timeline mutation performed."})
    events = sorted(events, key=lambda row: (row["activity_type"], row["related_item"] or ""))
    output = review_artifact("deterministic_review_activity_history_v1")
    output.update({"review_activity_history_id": deterministic_id("RACTREG", [row["activity_id"] for row in events]), "activities": events, "append_preserving_design": True, "summary": {"activity_count": len(events)}})
    return output
