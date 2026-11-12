"""Governance-sensitive conflict analysis."""

from __future__ import annotations

from reviewer_adjudication import adjudication_artifact
from review_operational_common import severity_rank
from stability import deterministic_id


def build_governance_conflict_analysis(conflicts: dict, rationale_diff_registry: dict) -> dict:
    diffs = {row.get("conflict_id"): row for row in rationale_diff_registry.get("rationale_diffs") or []}
    rows = []
    for conflict in conflicts.get("conflicts") or []:
        diff = diffs.get(conflict.get("conflict_id")) or {}
        categories = _categories(conflict, diff)
        rows.append(
            {
                "governance_conflict_id": deterministic_id("GCA", conflict.get("conflict_id"), categories),
                "conflict_id": conflict.get("conflict_id"),
                "source_item_id": conflict.get("source_item_id"),
                "conflict_type": conflict.get("conflict_type"),
                "governance_conflict_categories": categories,
                "governance_severity": _severity(conflict, categories),
                "governance_impact_summary": _impact_summary(categories),
                "requires_governance_reviewer": bool(conflict.get("governance_relevance") or categories),
                "requires_arbitration": "blocker_disagreement" in categories or "escalation_disagreement" in categories,
                "manual_review_required": True,
                "autonomous_governance_change": False,
            }
        )
    artifact = adjudication_artifact("deterministic_governance_conflict_analysis_v1")
    artifact.update({"governance_conflict_analysis_id": deterministic_id("GCAREG", [row["governance_conflict_id"] for row in rows]), "governance_conflicts": rows, "summary": {"governance_conflict_count": len(rows), "arbitration_required_count": sum(1 for row in rows if row["requires_arbitration"])}})
    return artifact


def _categories(conflict: dict, diff: dict) -> list[str]:
    categories = []
    ctype = conflict.get("conflict_type")
    if ctype == "conflicting_reviewer_decisions":
        categories.append("blocker_disagreement")
    if ctype == "conflicting_escalation_states":
        categories.append("escalation_disagreement")
    if "insufficient evidence references" in (diff.get("unresolved_ambiguity") or []):
        categories.append("evidence_sufficiency_disagreement")
    if diff.get("governance_disagreement"):
        categories.append("governance_disagreement")
    if ctype == "conflicting_rationale":
        categories.append("review_completeness_disagreement")
    return categories or ["reviewer_disagreement"]


def _severity(conflict: dict, categories: list[str]) -> str:
    if "blocker_disagreement" in categories or "escalation_disagreement" in categories:
        return "critical"
    return conflict.get("severity") or ("high" if severity_rank(conflict.get("severity")) >= 4 else "medium")


def _impact_summary(categories: list[str]) -> str:
    return "Manual governance review required for: " + ", ".join(categories) + ". No autonomous governance disposition is applied."
