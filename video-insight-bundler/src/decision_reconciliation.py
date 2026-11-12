"""Reconcile validated human decisions with Tier 1 blocker state."""

from __future__ import annotations

from copy import deepcopy

from blocker_disposition import NON_BLOCKING_DISPOSITIONS, disposition_is_unresolved
from intelligence_common import base_artifact, deterministic_id


def reconcile_decisions(validated_human_decisions: dict, tier_1_blocker_disposition: dict) -> dict:
    decisions_by_blocker = {}
    for decision in validated_human_decisions.get("validated_decisions") or []:
        decisions_by_blocker.setdefault(decision.get("blocker_id"), []).append(decision)
    rows = []
    for blocker in tier_1_blocker_disposition.get("blocker_dispositions", []):
        decision = _choose_decision(decisions_by_blocker.get(blocker.get("blocker_id")) or [])
        if not decision:
            rows.append(_row(blocker, None, False, "no_valid_decision", "No schema-valid human decision was supplied.", "cap_remains_active"))
            continue
        disposition = decision.get("disposition")
        clears = disposition in NON_BLOCKING_DISPOSITIONS
        if disposition == "proposed":
            rows.append(_row(blocker, decision, False, "proposed_keeps_blocker_active", "proposed never clears a blocker.", "cap_remains_active"))
        elif disposition == "confirmed_blocker":
            rows.append(_row(blocker, decision, False, "confirmed_blocker_keeps_cap_active", "confirmed_blocker keeps the Tier 1 cap active.", "cap_remains_active"))
        elif disposition == "deferred":
            rows.append(_row(blocker, decision, False, "deferred_keeps_cap_active", "deferred keeps the Tier 1 cap active by default.", "cap_remains_active"))
        elif clears:
            rows.append(_row(blocker, decision, True, "accepted_for_reassessment", "Validated clearing decision may be considered by reassessment.", "cap_lift_candidate"))
        else:
            rows.append(_row(blocker, decision, False, "unsupported_reconciliation_status", "Disposition is valid but not a clearing disposition.", "cap_remains_active"))

    artifact = base_artifact(method="deterministic_decision_reconciliation_v1")
    artifact.update(
        {
            "decision_reconciliation_id": deterministic_id("DREC", [(row.get("blocker_id"), row.get("decision_id"), row.get("reconciliation_status")) for row in rows]),
            "source_validated_human_decisions_ref": "governance/validated_human_decisions.json",
            "source_tier_1_disposition_ref": "governance/tier_1_blocker_disposition.json",
            "reconciled_decisions": rows,
            "summary": {
                "reconciled_blocker_count": len(rows),
                "accepted_for_reassessment_count": sum(1 for row in rows if row.get("accepted_for_reassessment")),
                "unresolved_after_reconciliation_count": sum(1 for row in rows if not row.get("accepted_for_reassessment")),
            },
        }
    )
    return artifact


def build_reconciled_tier_1_disposition(tier_1_blocker_disposition: dict, decision_reconciliation: dict) -> dict:
    output = deepcopy(tier_1_blocker_disposition)
    reconciliation_by_blocker = {row.get("blocker_id"): row for row in decision_reconciliation.get("reconciled_decisions") or []}
    for row in output.get("blocker_dispositions", []):
        rec = reconciliation_by_blocker.get(row.get("blocker_id"))
        if rec and rec.get("accepted_for_reassessment"):
            row["disposition"] = rec.get("proposed_new_disposition")
            row["decision_evidence_refs"] = rec.get("evidence_refs") or []
            row["human_decision_id"] = rec.get("decision_id")
            row["reconciliation_status"] = rec.get("reconciliation_status")
    blockers = output.get("blocker_dispositions") or []
    unresolved = [row for row in blockers if disposition_is_unresolved(row)]
    output["method"] = "deterministic_reconciled_tier_1_blocker_disposition_v1"
    output["tier_1_blocker_disposition_id"] = deterministic_id("T1DISPREC", [(row.get("blocker_id"), row.get("disposition"), row.get("human_decision_id")) for row in blockers])
    output["source_raw_tier_1_disposition_ref"] = "governance/tier_1_blocker_disposition.json"
    output["source_decision_reconciliation_ref"] = "governance/decision_reconciliation.json"
    output["summary"] = {
        **(output.get("summary") or {}),
        "tier_1_blocker_count": len(blockers),
        "unresolved_tier_1_blocker_count": len(unresolved),
        "resolved_or_non_blocking_count": len(blockers) - len(unresolved),
        "readiness_cap_lifted": bool(blockers) and not unresolved,
    }
    return output


def _choose_decision(decisions: list[dict]) -> dict | None:
    order = {"resolved": 0, "externally_reviewed": 1, "false_positive": 2, "accepted_risk": 3, "confirmed_blocker": 4, "deferred": 5, "proposed": 6}
    if not decisions:
        return None
    return sorted(decisions, key=lambda row: (order.get(row.get("disposition"), 99), row.get("decision_id") or ""))[0]


def _row(blocker: dict, decision: dict | None, accepted: bool, status: str, reason: str, effect: str) -> dict:
    disposition = (decision or {}).get("disposition") or blocker.get("disposition")
    return {
        "blocker_id": blocker.get("blocker_id"),
        "prior_disposition": blocker.get("disposition"),
        "proposed_new_disposition": disposition,
        "decision_id": (decision or {}).get("decision_id"),
        "accepted_for_reassessment": accepted,
        "reconciliation_status": status,
        "reason": reason,
        "evidence_refs": (decision or {}).get("evidence_refs") or [],
        "readiness_effect_candidate": effect,
    }
