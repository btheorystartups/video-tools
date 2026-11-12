"""Operational review completion workflow tracking."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id


def build_review_completion_registry(state_registry: dict, followups: dict, escalations: dict) -> dict:
    unresolved_followups = followups.get("followup_items") or []
    remaining_escalations = escalations.get("escalation_items") or []
    workflows = []
    for name in ["pacing review", "governance review", "blocker review", "escalation review", "executive review"]:
        complete = not remaining_escalations if "escalation" in name else not unresolved_followups if "executive" in name else False
        workflow_id = deterministic_id("RCOMP", name, complete)
        workflows.append({"completion_id": workflow_id, "review_type": name, "completed_steps": [] if not complete else ["human_review_recorded"], "completion_status": "completed" if complete else "pending", "unresolved_followups": [row.get("followup_id") for row in unresolved_followups[:20]], "remaining_blockers": [row.get("item_id") for row in state_registry.get("state_items") or [] if row.get("item_type") == "blocker" and row.get("review_state") != "resolved"], "remaining_escalations": [row.get("escalation_id") for row in remaining_escalations], "review_confidence": "limited_until_human_completion", "next_required_review": "Capture reviewer decision and rationale."})
    output = review_artifact("deterministic_review_completion_registry_v1")
    output.update({"review_completion_registry_id": deterministic_id("RCOMPREG", [row["completion_id"] for row in workflows]), "completion_workflows": workflows, "summary": {"workflow_count": len(workflows), "pending_count": sum(1 for row in workflows if row["completion_status"] != "completed")}})
    return output
