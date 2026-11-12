"""Governed reviewer adjudication records for reconciliation conflicts."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id

ADJUDICATION_LIMITATION = (
    "This system provides deterministic reviewer adjudication and governance-conflict workflow support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer "
    "behavior, or make autonomous editorial decisions. Human review is required."
)


def adjudication_artifact(method: str) -> dict:
    artifact = review_artifact(method)
    artifact["limitations"] = [ADJUDICATION_LIMITATION]
    return artifact


def build_reviewer_adjudication_registry(conflict_resolution_registry: dict, rationale_diff_registry: dict, governance_conflict_analysis: dict) -> dict:
    diffs = {row.get("conflict_id"): row for row in rationale_diff_registry.get("rationale_diffs") or []}
    impacts = {row.get("conflict_id"): row for row in governance_conflict_analysis.get("governance_conflicts") or []}
    rows = []
    for workflow in conflict_resolution_registry.get("conflict_resolution_workflows") or []:
        conflict_id = workflow.get("conflict_id")
        impact = impacts.get(conflict_id) or {}
        diff = diffs.get(conflict_id) or {}
        rows.append(
            {
                "adjudication_id": deterministic_id("ADJ", conflict_id, workflow.get("workflow_id")),
                "conflict_id": conflict_id,
                "adjudicating_reviewer": None,
                "adjudicating_role": "manual_adjudicator_required",
                "rationale": None,
                "reviewer_rationales_considered": diff.get("rationale_texts") or [],
                "evidence_considered": diff.get("evidence_refs") or [],
                "governance_impact": impact.get("governance_impact_summary", "pending human governance review"),
                "unresolved_concerns": workflow.get("unresolved_questions") or [],
                "escalation_state": workflow.get("resolution_state"),
                "final_disposition": "pending_human_adjudication",
                "follow_up_requirements": workflow.get("required_manual_actions") or [],
                "operational_state_mutated": False,
                "autonomous_resolution_performed": False,
            }
        )
    artifact = adjudication_artifact("deterministic_reviewer_adjudication_registry_v1")
    artifact.update(
        {
            "reviewer_adjudication_registry_id": deterministic_id("ADJREG", [row["adjudication_id"] for row in rows]),
            "adjudications": rows,
            "summary": {
                "adjudication_count": len(rows),
                "pending_human_adjudication_count": len(rows),
                "operational_state_mutated": False,
            },
        }
    )
    return artifact
