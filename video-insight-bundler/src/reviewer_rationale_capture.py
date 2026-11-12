"""Structured reviewer rationale registry."""

from __future__ import annotations

from review_operational_common import review_artifact, stable_timestamp
from stability import deterministic_id


def build_reviewer_rationale_registry(annotations: dict) -> dict:
    rationales = []
    for row in annotations.get("annotations") or []:
        if row.get("annotation_type") not in {"accepted_risk_rationale", "preserve_as_intentional_rationale", "escalation_note", "blocker_annotation", "recommendation_annotation"}:
            continue
        related = row.get("related_recommendation") or row.get("related_blocker") or row.get("related_segment")
        rationale_id = deterministic_id("RAT", row.get("annotation_id"), related)
        rationales.append(
            {
                "rationale_id": rationale_id,
                "related_item": related,
                "rationale_type": row.get("annotation_type"),
                "reviewer_summary": row.get("annotation_text"),
                "supporting_evidence": row.get("evidence_refs") or [],
                "governance_impact": "requires_human_review" if row.get("escalation_required") else "review_context_only",
                "followup_required": bool(row.get("followup_required")),
                "escalation_required": bool(row.get("escalation_required")),
                "timestamp": stable_timestamp(rationale_id),
            }
        )
    output = review_artifact("deterministic_reviewer_rationale_registry_v1")
    output.update({"reviewer_rationale_registry_id": deterministic_id("RATREG", [row["rationale_id"] for row in rationales]), "rationales": rationales, "summary": {"rationale_count": len(rationales), "followup_required_count": sum(1 for row in rationales if row["followup_required"])}})
    return output
