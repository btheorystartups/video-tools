"""Explicit consensus-required workflow scaffolding."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id

CONSENSUS_STATES = ["no_consensus", "partial_consensus", "governance_consensus_pending", "escalation_consensus_pending", "consensus_reached_with_rationale"]


def build_consensus_workflow_registry(conflict_resolution_registry: dict, rationale_diff_registry: dict, governance_conflict_analysis: dict) -> dict:
    diffs = {row.get("conflict_id"): row for row in rationale_diff_registry.get("rationale_diffs") or []}
    impacts = {row.get("conflict_id"): row for row in governance_conflict_analysis.get("governance_conflicts") or []}
    rows = []
    for workflow in conflict_resolution_registry.get("conflict_resolution_workflows") or []:
        conflict_id = workflow.get("conflict_id")
        state = _state(workflow, impacts.get(conflict_id) or {})
        rows.append(
            {
                "consensus_workflow_id": deterministic_id("CON", conflict_id, state),
                "conflict_id": conflict_id,
                "consensus_state": state,
                "allowed_consensus_states": CONSENSUS_STATES,
                "rationale_conflicts": (diffs.get(conflict_id) or {}).get("rationale_conflicts") or [],
                "required_participants": workflow.get("reviewer_role_context") or ["reviewer"],
                "consensus_rationale": None,
                "manual_consensus_required": True,
                "autonomous_consensus_performed": False,
            }
        )
    artifact = adjudication_artifact("deterministic_consensus_workflow_registry_v1")
    artifact.update({"consensus_workflow_registry_id": deterministic_id("CONREG", [row["consensus_workflow_id"] for row in rows]), "consensus_workflows": rows, "summary": {"consensus_workflow_count": len(rows), "pending_consensus_count": sum(1 for row in rows if row["consensus_state"] != "consensus_reached_with_rationale")}})
    return artifact


def _state(workflow: dict, impact: dict) -> str:
    if impact.get("requires_arbitration"):
        return "escalation_consensus_pending"
    if workflow.get("resolution_state") == "governance_review_required":
        return "governance_consensus_pending"
    return "no_consensus"
