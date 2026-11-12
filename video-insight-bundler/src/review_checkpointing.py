"""Saved review checkpoint generation."""

from __future__ import annotations

from review_operational_common import review_artifact, stable_timestamp
from stability import deterministic_id


def build_review_checkpoints(state_registry: dict, annotations: dict, queue_registry: dict) -> dict:
    checkpoints = []
    specs = [
        ("pacing review checkpoint", "visualizations/review/review_queue_dashboard.html", "continue pacing review"),
        ("governance checkpoint", "visualizations/review/escalation_dashboard.html", "continue governance escalation workflow"),
        ("blocker-review checkpoint", "visualizations/review/review_queue_dashboard.html", "continue unresolved blocker review"),
        ("rhetorical-review checkpoint", "visualizations/review/reviewer_annotations.html", "continue rhetorical review annotations"),
        ("executive-review checkpoint", "visualizations/review/printable_review_packet_index.html", "open printable executive packet"),
    ]
    unresolved = [row.get("item_id") for row in state_registry.get("state_items") or [] if row.get("review_state") in {"followup_required", "escalation_required", "in_review"}]
    queue_items = queue_registry.get("queue_items") or []
    for name, page, action in specs:
        checkpoint_id = deterministic_id("RCHK", name, unresolved[:10], [row.get("queue_id") for row in queue_items[:5]])
        checkpoints.append({"checkpoint_id": checkpoint_id, "checkpoint_name": name, "current_page": page, "current_video": (queue_items[0].get("related_artifact") if queue_items else None), "current_segment": ((queue_items[0].get("related_segments") or [None])[0] if queue_items else None), "current_filters": ["open", "followup_required", "escalation_required"], "current_review_state": "in_review", "pending_actions": unresolved[:20], "next_recommended_action": action, "unresolved_items": unresolved[:20], "related_annotations": [row.get("annotation_id") for row in (annotations.get("annotations") or [])[:20]], "timestamp": stable_timestamp(checkpoint_id)})
    output = review_artifact("deterministic_review_checkpoints_v1")
    output.update({"review_checkpoints_id": deterministic_id("RCHKREG", [row["checkpoint_id"] for row in checkpoints]), "checkpoints": checkpoints, "summary": {"checkpoint_count": len(checkpoints), "unresolved_item_count": len(unresolved)}})
    return output
