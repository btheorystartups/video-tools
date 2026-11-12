"""Gate reassessment movement to validated human decisions only."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_reassessment_gatekeeper(validated_human_decisions: dict, rejected_human_decisions: dict, decision_reconciliation: dict, governance_diagnostics: dict | None = None) -> dict:
    accepted = [row for row in decision_reconciliation.get("reconciled_decisions") or [] if row.get("accepted_for_reassessment")]
    unresolved = [row for row in decision_reconciliation.get("reconciled_decisions") or [] if not row.get("accepted_for_reassessment")]
    failed_thresholds = [row for row in (governance_diagnostics or {}).get("failed_thresholds", []) if row.get("threshold_id") not in {"compressed_tier_1_blockers", "hard_blocker_count"}]
    valid_count = (validated_human_decisions.get("summary") or {}).get("valid_decision_count", 0)
    rejected_count = (rejected_human_decisions.get("summary") or {}).get("rejected_decision_count", 0)
    clearing_count = len(accepted)
    unresolved_count = len(unresolved)
    readiness_can_change = bool(clearing_count and unresolved_count == 0 and not failed_thresholds)
    artifact = base_artifact(method="deterministic_reassessment_gatekeeper_v1")
    artifact.update(
        {
            "reassessment_gatekeeper_id": deterministic_id("RGATE", valid_count, rejected_count, [(row.get("blocker_id"), row.get("accepted_for_reassessment")) for row in decision_reconciliation.get("reconciled_decisions") or []]),
            "valid_decision_count": valid_count,
            "rejected_decision_count": rejected_count,
            "clearing_decision_count": clearing_count,
            "unresolved_blocker_count": unresolved_count,
            "cap_lift_candidates": [{"blocker_id": row.get("blocker_id"), "decision_id": row.get("decision_id")} for row in accepted],
            "cap_still_active_reasons": _cap_reasons(unresolved, rejected_count, failed_thresholds),
            "reassessment_allowed": True,
            "readiness_can_change": readiness_can_change,
            "classification_can_change": readiness_can_change,
            "gatekeeper_explanation": _explain(clearing_count, unresolved_count, rejected_count, failed_thresholds, readiness_can_change),
            "summary": {
                "readiness_remains_capped": not readiness_can_change,
                "invalid_decisions_affect_readiness": False,
                "all_tier_1_blockers_validly_cleared": bool(clearing_count and unresolved_count == 0),
            },
        }
    )
    return artifact


def _cap_reasons(unresolved: list[dict], rejected_count: int, failed_thresholds: list[dict]) -> list[str]:
    reasons = []
    if unresolved:
        reasons.append("One or more Tier 1 blockers remain unresolved after validated decision reconciliation.")
    if rejected_count:
        reasons.append("Rejected decisions cannot influence readiness.")
    if failed_thresholds:
        reasons.append("One or more non-Tier 1 governance thresholds still fail.")
    if not reasons:
        reasons.append("No cap still active from human decision intake.")
    return reasons


def _explain(clearing_count: int, unresolved_count: int, rejected_count: int, failed_thresholds: list[dict], readiness_can_change: bool) -> str:
    if readiness_can_change:
        return "All Tier 1 blockers have validated clearing decisions and no other governance thresholds block movement."
    if not clearing_count:
        return "No valid clearing decisions exist, so readiness remains capped."
    if unresolved_count:
        return "Some blockers have valid clearing decisions, but unresolved Tier 1 blockers remain."
    if rejected_count:
        return "Only validated decisions may affect readiness; rejected decisions are audit-only."
    if failed_thresholds:
        return "Human decisions cleared Tier 1 candidates, but other governance thresholds still block movement."
    return "Readiness remains capped by conservative gatekeeper policy."
