"""Deterministic governance reassessment after human dispositions."""

from __future__ import annotations

from blocker_disposition import disposition_is_unresolved
from intelligence_common import base_artifact, deterministic_id
from readiness_delta_analysis import analyze_readiness_delta


def build_governance_reassessment(before_arbitration: dict, after_arbitration: dict, before_diagnostics: dict, after_diagnostics: dict, blocker_analysis: dict, tier_1_blocker_disposition: dict, compressed_review_queue: dict) -> dict:
    rows = tier_1_blocker_disposition.get("blocker_dispositions", [])
    resolved = [row for row in rows if not disposition_is_unresolved(row)]
    remaining = [row for row in rows if disposition_is_unresolved(row)]
    reclassified = [
        {
            "blocker_id": row.get("blocker_id"),
            "disposition": row.get("disposition"),
            "decision_evidence_refs": row.get("decision_evidence_refs") or [],
        }
        for row in resolved
    ]
    thresholds_failing = [row for row in after_diagnostics.get("failed_thresholds", []) if row.get("status") != "pass"]
    readiness_changed = before_arbitration.get("classification") != after_arbitration.get("classification") or before_arbitration.get("arbitrated_readiness_score") != after_arbitration.get("arbitrated_readiness_score")
    reassessment = base_artifact(method="deterministic_governance_reassessment_v1")
    reassessment.update(
        {
            "governance_reassessment_id": deterministic_id("GREASSESS", before_arbitration.get("readiness_arbitration_id"), after_arbitration.get("readiness_arbitration_id"), [(row.get("blocker_id"), row.get("disposition")) for row in rows]),
            "source_readiness_before_ref": "governance/readiness_arbitration.json",
            "source_tier_1_disposition_ref": "governance/tier_1_blocker_disposition.json",
            "blockers_resolved": [{"blocker_id": row.get("blocker_id"), "disposition": row.get("disposition"), "decision_evidence_refs": row.get("decision_evidence_refs") or []} for row in resolved],
            "blockers_remaining": [{"blocker_id": row.get("blocker_id"), "disposition": row.get("disposition"), "evidence_refs": row.get("evidence_refs") or []} for row in remaining],
            "blockers_reclassified": reclassified,
            "readiness_delta": {
                "before": before_arbitration.get("arbitrated_readiness_score"),
                "after": after_arbitration.get("arbitrated_readiness_score"),
                "delta": round((after_arbitration.get("arbitrated_readiness_score") or 0.0) - (before_arbitration.get("arbitrated_readiness_score") or 0.0), 3),
            },
            "classification_delta": {"before": before_arbitration.get("classification"), "after": after_arbitration.get("classification")},
            "thresholds_changed": _changed_thresholds(before_diagnostics, after_diagnostics),
            "thresholds_still_failing": thresholds_failing,
            "evidence_refs": sorted(set(ref for row in rows for ref in (row.get("evidence_refs") or []) + (row.get("decision_evidence_refs") or []))),
            "why_readiness_changed": _why_changed(readiness_changed, remaining),
            "why_readiness_did_not_change": _why_not_changed(readiness_changed, remaining, thresholds_failing),
            "hardening_cap_active": bool(remaining or thresholds_failing),
            "summary": {
                "blockers_resolved_count": len(resolved),
                "blockers_remaining_count": len(remaining),
                "thresholds_still_failing_count": len(thresholds_failing),
                "readiness_changed": readiness_changed,
                "readiness_remains_capped": bool(remaining or thresholds_failing),
                "classification": after_arbitration.get("classification"),
            },
        }
    )
    delta = analyze_readiness_delta(before_arbitration, after_arbitration, before_diagnostics, after_diagnostics, tier_1_blocker_disposition, tier_1_blocker_disposition, compressed_review_queue)
    return {"governance_reassessment": reassessment, "governance_reassessment_delta": delta}


def _changed_thresholds(before: dict, after: dict) -> list[dict]:
    before_map = {row.get("threshold_id"): row for row in before.get("thresholds", [])}
    after_map = {row.get("threshold_id"): row for row in after.get("thresholds", [])}
    rows = []
    for threshold_id in sorted(set(before_map) | set(after_map)):
        left = before_map.get(threshold_id, {})
        right = after_map.get(threshold_id, {})
        if left.get("status") != right.get("status") or left.get("gap_to_pass") != right.get("gap_to_pass"):
            rows.append({"threshold_id": threshold_id, "before_status": left.get("status"), "after_status": right.get("status"), "before_gap_to_pass": left.get("gap_to_pass"), "after_gap_to_pass": right.get("gap_to_pass")})
    return rows


def _why_changed(changed: bool, remaining: list[dict]) -> list[str]:
    if not changed:
        return []
    reasons = ["Governance reassessment inputs changed the readiness score or classification."]
    if remaining:
        reasons.append("Readiness remains capped because unresolved Tier 1 blockers remain.")
    return reasons


def _why_not_changed(changed: bool, remaining: list[dict], thresholds: list[dict]) -> list[str]:
    if changed:
        return []
    reasons = ["Readiness did not change because reassessment found no evidence-backed removal of hard governance blockers."]
    if remaining:
        reasons.append("Tier 1 blocker dispositions remain proposed, deferred, confirmed, or evidence-incomplete.")
    if thresholds:
        reasons.append("One or more governance thresholds still fail after reassessment.")
    return reasons
