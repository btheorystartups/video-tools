"""Reviewer-role-aware workflow labels without hidden permission systems."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from stability import deterministic_id

ROLES = ["reviewer", "escalation reviewer", "governance reviewer", "arbitration reviewer", "executive reviewer"]


def build_reviewer_role_resolution(conflicts: dict) -> dict:
    rows = []
    for conflict in conflicts.get("conflicts") or []:
        roles = ["reviewer"]
        if conflict.get("conflict_type") == "conflicting_escalation_states":
            roles.append("escalation reviewer")
        if conflict.get("governance_relevance"):
            roles.append("governance reviewer")
        if conflict.get("severity") == "high":
            roles.append("arbitration reviewer")
        rows.append(
            {
                "role_resolution_id": deterministic_id("RROLE", conflict.get("conflict_id"), roles),
                "conflict_id": conflict.get("conflict_id"),
                "available_roles": ROLES,
                "recommended_roles": roles,
                "role_model_type": "informational_workflow_label_only",
                "permission_enforcement": False,
                "hidden_permission_system": False,
            }
        )
    artifact = adjudication_artifact("deterministic_reviewer_role_resolution_v1")
    artifact.update({"reviewer_role_resolution_id": deterministic_id("RROLEREG", [row["role_resolution_id"] for row in rows]), "role_resolution_items": rows, "summary": {"role_resolution_count": len(rows)}})
    return artifact
