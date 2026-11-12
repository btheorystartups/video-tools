"""Explicit local review session memory artifacts."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id


def build_review_session_registry(state_registry: dict, checkpoints: dict, followups: dict, escalations: dict, queue_registry: dict) -> dict:
    checkpoint = ((checkpoints.get("checkpoints") or [{}])[0])
    queue = ((queue_registry.get("queue_items") or [{}])[0])
    session = review_artifact("deterministic_review_session_registry_v1")
    session.update(
        {
            "review_session_registry_id": deterministic_id("RSESS", checkpoint.get("checkpoint_id"), queue.get("queue_id")),
            "sessions": [
                {
                    "session_id": deterministic_id("RSESSITEM", checkpoint.get("checkpoint_id")),
                    "reviewer_id": "local_reviewer_placeholder",
                    "last_reviewed_segment": checkpoint.get("current_segment"),
                    "last_opened_timeline": checkpoint.get("current_page"),
                    "last_review_journey": "governance_blocker_review" if escalations.get("escalation_items") else "timeline_segment_review",
                    "unresolved_items": checkpoint.get("unresolved_items") or [],
                    "active_filters": checkpoint.get("current_filters") or [],
                    "pending_decisions": [row.get("item_id") for row in state_registry.get("state_items") or [] if row.get("review_state") in {"in_review", "escalation_required"}],
                    "pending_followups": [row.get("followup_id") for row in followups.get("followup_items") or []],
                    "active_escalation_paths": [row.get("escalation_id") for row in escalations.get("escalation_items") or []],
                    "review_completion_state": "pending" if followups.get("followup_items") or escalations.get("escalation_items") else "ready_for_human_completion_review",
                }
            ],
            "summary": {"session_count": 1, "pending_followup_count": len(followups.get("followup_items") or []), "active_escalation_count": len(escalations.get("escalation_items") or [])},
        }
    )
    return session


def build_review_progress_summary(state_registry: dict, completion: dict, followups: dict, escalations: dict) -> dict:
    states = state_registry.get("state_items") or []
    summary = review_artifact("deterministic_review_progress_summary_v1")
    reviewed = sum(1 for row in states if row.get("review_state") in {"reviewed", "resolved", "externally_reviewed"})
    total = len(states)
    summary.update({"review_progress_summary_id": deterministic_id("RPROG", total, reviewed, len(followups.get("followup_items") or [])), "reviewed_item_count": reviewed, "total_review_item_count": total, "open_followup_count": len(followups.get("followup_items") or []), "open_escalation_count": len(escalations.get("escalation_items") or []), "completion_pending_count": (completion.get("summary") or {}).get("pending_count", 0), "progress_ratio": round(reviewed / total, 3) if total else 0.0, "summary": {"reviewed_item_count": reviewed, "total_review_item_count": total}})
    return summary
