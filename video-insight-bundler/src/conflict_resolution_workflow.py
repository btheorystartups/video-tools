"""Manual conflict resolution workflow scaffolding."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id

RESOLUTION_STATES = [
    "unresolved",
    "under_review",
    "escalation_required",
    "governance_review_required",
    "consensus_required",
    "partially_resolved",
    "resolved_with_rationale",
    "deferred",
]


def build_conflict_resolution_registry(conflicts: dict, queues: dict, role_registry: dict | None = None) -> dict:
    queue_ids = {row.get("conflict_id"): row.get("queue_id") for row in queues.get("unresolved_conflict_queue", {}).get("queue_items") or []}
    roles = {row.get("conflict_id"): row for row in (role_registry or {}).get("role_resolution_items") or []}
    workflows = []
    for conflict in conflicts.get("conflicts") or []:
        state = _initial_state(conflict)
        conflict_id = conflict.get("conflict_id")
        workflows.append(
            {
                "workflow_id": deterministic_id("CWF", conflict_id, state),
                "conflict_id": conflict_id,
                "source_item_id": conflict.get("source_item_id"),
                "conflict_type": conflict.get("conflict_type"),
                "resolution_state": state,
                "allowed_resolution_states": RESOLUTION_STATES,
                "queue_ref": queue_ids.get(conflict_id),
                "reviewer_role_context": roles.get(conflict_id, {}).get("recommended_roles", ["reviewer"]),
                "required_manual_actions": _manual_actions(conflict),
                "unresolved_questions": _questions(conflict),
                "append_only_history_required": True,
                "autonomous_resolution_performed": False,
                "operational_state_mutated": False,
            }
        )
    artifact = adjudication_artifact("deterministic_conflict_resolution_workflow_v1")
    artifact.update(
        {
            "conflict_resolution_registry_id": deterministic_id("CWFREG", [row["workflow_id"] for row in workflows]),
            "conflict_resolution_workflows": workflows,
            "summary": {
                "workflow_count": len(workflows),
                "unresolved_count": sum(1 for row in workflows if row["resolution_state"] != "resolved_with_rationale"),
                "autonomous_resolution_count": 0,
            },
        }
    )
    return artifact


def _initial_state(conflict: dict) -> str:
    conflict_type = conflict.get("conflict_type")
    if conflict.get("governance_relevance"):
        return "governance_review_required"
    if conflict_type == "conflicting_escalation_states":
        return "escalation_required"
    if conflict_type in {"conflicting_reviewer_decisions", "conflicting_rationale"}:
        return "consensus_required"
    return "unresolved"


def _manual_actions(conflict: dict) -> list[str]:
    actions = ["Compare reviewer records side by side.", "Record human adjudication rationale before any operational state change."]
    if conflict.get("governance_relevance"):
        actions.append("Route to governance reviewer or arbitration reviewer.")
    if conflict.get("conflict_type") == "conflicting_escalation_states":
        actions.append("Confirm escalation state with an escalation reviewer.")
    return actions


def _questions(conflict: dict) -> list[str]:
    return [
        f"Which reviewer record, if any, has sufficient evidence for {conflict.get('source_item_id')}?",
        "What rationale should remain attached to the final human disposition?",
        "Does the conflict require escalation, governance review, or deferral?",
    ]
