"""Reviewer-editable import template definitions."""

from __future__ import annotations

from review_operational_common import REVIEW_LIMITATION

TEMPLATE_VERSION = "phase36_review_import_template_v1"

IMPORT_LIMITATION = (
    "This system provides deterministic editorial-review ingestion and reconciliation support. "
    "It does not autonomously resolve governance decisions, infer identity, diagnose emotion, "
    "predict viewer behavior, or make autonomous editorial decisions. Human review is required."
)

ALLOWED_REVIEW_STATES = {"open_review", "reviewed", "accepted", "rejected", "deferred", "requires_manual_review"}
ALLOWED_DECISIONS = {"accept", "reject", "defer", "accepted_risk", "preserve_as_intentional", "requires_escalation"}
ALLOWED_ESCALATION_STATES = {"none", "requested", "active", "resolved_by_human", "requires_governance_review"}


def template_fields(kind: str) -> list[str]:
    common = ["import_item_id", "reviewer_id", "source_item_id", "related_video", "related_segment", "related_recommendation", "related_blocker", "reviewer_notes"]
    if kind == "annotation":
        return common + ["annotation_type", "severity", "review_state", "followup_required", "escalation_state", "checkpoint_reference"]
    if kind == "decision":
        return common + ["decision", "decision_rationale", "governance_relevance", "escalation_state", "checkpoint_reference"]
    if kind == "followup":
        return common + ["followup_state", "required_action", "owner_placeholder", "escalation_state", "checkpoint_reference"]
    if kind == "rationale":
        return common + ["rationale_type", "rationale_text", "governance_relevance", "checkpoint_reference"]
    return common + ["escalation_state", "escalation_note", "governance_relevance", "checkpoint_reference"]


def build_template(kind: str, examples: list[dict] | None = None) -> dict:
    return {
        "template_version": TEMPLATE_VERSION,
        "template_type": kind,
        "instructions": [
            "Fill reviewer-authored fields only; do not edit source_item_id values unless creating a new item.",
            "Leave unknown references blank instead of inventing links.",
            "Conflicting decisions are imported as unresolved reconciliation conflicts, not auto-resolved.",
        ],
        "allowed_values": {
            "review_state": sorted(ALLOWED_REVIEW_STATES),
            "decision": sorted(ALLOWED_DECISIONS),
            "escalation_state": sorted(ALLOWED_ESCALATION_STATES),
            "severity": ["review", "low", "medium", "high", "critical"],
        },
        "fields": template_fields(kind),
        "examples": examples or [],
        "governance_notes": [
            IMPORT_LIMITATION,
            REVIEW_LIMITATION,
            "Reviewer imports are append-preserving and never clear blockers without explicit validated human evidence.",
        ],
    }
