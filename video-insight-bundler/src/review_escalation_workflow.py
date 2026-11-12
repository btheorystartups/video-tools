"""Deterministic escalation workflow generation."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id


def build_review_escalation_registry(annotations: dict, outputs: dict) -> dict:
    items = []
    for row in annotations.get("annotations") or []:
        if not row.get("escalation_required"):
            continue
        escalation_type = "governance escalation" if row.get("related_blocker") else "high-risk recommendation" if row.get("related_recommendation") else "unresolved ambiguity"
        escalation_id = deterministic_id("ESC", row.get("annotation_id"), escalation_type)
        items.append(
            {
                "escalation_id": escalation_id,
                "related_artifact": row.get("related_recommendation") or row.get("related_blocker") or row.get("related_segment"),
                "escalation_type": escalation_type,
                "escalation_reason": row.get("annotation_text"),
                "severity": row.get("severity") or "high",
                "evidence_refs": row.get("evidence_refs") or [],
                "unresolved_questions": ["What human decision or evidence would close this review item?"],
                "required_followup": True,
                "suggested_reviewer_action": "Open the escalation packet, inspect evidence refs, and record a human decision or deferral rationale.",
            }
        )
    diagnostics = outputs.get("governance_diagnostics") or {}
    for threshold in diagnostics.get("thresholds") or []:
        if threshold.get("status") == "fail":
            escalation_id = deterministic_id("ESC", "threshold", threshold.get("threshold_id"))
            items.append({"escalation_id": escalation_id, "related_artifact": threshold.get("threshold_id"), "escalation_type": "governance escalation", "escalation_reason": threshold.get("explanation") or "Governance threshold requires review.", "severity": "high", "evidence_refs": ["governance/governance_diagnostics.json"], "unresolved_questions": ["Which governance evidence is sufficient for reassessment?"], "required_followup": True, "suggested_reviewer_action": "Review governance diagnostics before promotion."})
    output = review_artifact("deterministic_review_escalation_registry_v1")
    output.update({"review_escalation_registry_id": deterministic_id("ESCREG", [row["escalation_id"] for row in items]), "escalation_items": items, "summary": {"escalation_count": len(items)}})
    return output
