"""Deterministic explanations for governance readiness movement."""

from __future__ import annotations

from blocker_disposition import disposition_is_unresolved
from intelligence_common import base_artifact, deterministic_id, num


def _classification_rank(value: str | None) -> int:
    order = {"not_ready": 0, "beta_plus": 1, "rc_candidate": 2, "release_candidate": 3}
    return order.get(value or "not_ready", 0)


def _threshold_map(diagnostics: dict) -> dict[str, dict]:
    return {row.get("threshold_id"): row for row in diagnostics.get("thresholds", []) if row.get("threshold_id")}


def analyze_readiness_delta(before_arbitration: dict, after_arbitration: dict, before_diagnostics: dict, after_diagnostics: dict, before_dispositions: dict, after_dispositions: dict, compressed_review_queue: dict | None = None) -> dict:
    before_score = num(before_arbitration.get("arbitrated_readiness_score"))
    after_score = num(after_arbitration.get("arbitrated_readiness_score"))
    before_class = before_arbitration.get("classification") or "not_ready"
    after_class = after_arbitration.get("classification") or "not_ready"
    before_thresholds = _threshold_map(before_diagnostics)
    after_thresholds = _threshold_map(after_diagnostics)
    threshold_movement = []
    for threshold_id in sorted(set(before_thresholds) | set(after_thresholds)):
        before = before_thresholds.get(threshold_id, {})
        after = after_thresholds.get(threshold_id, {})
        threshold_movement.append(
            {
                "threshold_id": threshold_id,
                "before_status": before.get("status"),
                "after_status": after.get("status"),
                "before_gap_to_pass": before.get("gap_to_pass"),
                "after_gap_to_pass": after.get("gap_to_pass"),
                "movement": round(num(before.get("gap_to_pass")) - num(after.get("gap_to_pass")), 3),
                "evidence_refs": sorted(set((before.get("evidence_refs") or []) + (after.get("evidence_refs") or []))),
            }
        )

    before_rows = {row.get("blocker_id"): row for row in before_dispositions.get("blocker_dispositions", []) if row.get("blocker_id")}
    after_rows = {row.get("blocker_id"): row for row in after_dispositions.get("blocker_dispositions", []) if row.get("blocker_id")}
    blocker_movement = []
    for blocker_id in sorted(set(before_rows) | set(after_rows)):
        before = before_rows.get(blocker_id, {})
        after = after_rows.get(blocker_id, {})
        blocker_movement.append(
            {
                "blocker_id": blocker_id,
                "before_disposition": before.get("disposition"),
                "after_disposition": after.get("disposition"),
                "before_unresolved": disposition_is_unresolved(before) if before else None,
                "after_unresolved": disposition_is_unresolved(after) if after else None,
                "decision_evidence_refs": after.get("decision_evidence_refs") or [],
            }
        )

    review_queue_changes = {
        "tier_1_blocker_count": ((compressed_review_queue or {}).get("summary") or {}).get("tier_1_blocker_count", 0),
        "compressed_review_item_count": ((compressed_review_queue or {}).get("summary") or {}).get("compressed_review_item_count", 0),
        "raw_review_item_count": ((compressed_review_queue or {}).get("summary") or {}).get("raw_review_item_count", 0),
    }
    unresolved_after = sum(1 for row in after_rows.values() if disposition_is_unresolved(row))
    severity_before = (before_diagnostics.get("summary") or {}).get("hard_blocker_count", 0)
    severity_after = (after_diagnostics.get("summary") or {}).get("hard_blocker_count", 0)
    explained = bool(threshold_movement or blocker_movement or before_score == after_score)
    output = base_artifact(method="deterministic_readiness_delta_analysis_v1")
    output.update(
        {
            "readiness_delta_analysis_id": deterministic_id("RDELTA", before_arbitration.get("readiness_arbitration_id"), after_arbitration.get("readiness_arbitration_id"), [(row["blocker_id"], row.get("after_disposition")) for row in blocker_movement]),
            "readiness_before": {"score": before_score, "classification": before_class},
            "readiness_after": {"score": after_score, "classification": after_class},
            "readiness_delta": round(after_score - before_score, 3),
            "classification_delta": {
                "before": before_class,
                "after": after_class,
                "rank_delta": _classification_rank(after_class) - _classification_rank(before_class),
            },
            "threshold_movement": threshold_movement,
            "blocker_movement": blocker_movement,
            "review_queue_changes": review_queue_changes,
            "remediation_disposition_changes": blocker_movement,
            "confidence_movement": {
                "before_governance_readiness": before_arbitration.get("governance_readiness"),
                "after_governance_readiness": after_arbitration.get("governance_readiness"),
            },
            "governance_severity_movement": {
                "before_hard_blocker_count": severity_before,
                "after_hard_blocker_count": severity_after,
                "movement": severity_after - severity_before,
            },
            "unexplained_readiness_jump": (after_score != before_score or before_class != after_class) and not explained,
            "why_readiness_changed": _why_changed(before_score, after_score, before_class, after_class, unresolved_after),
            "why_readiness_did_not_change": _why_not_changed(before_score, after_score, before_class, after_class, unresolved_after),
            "summary": {
                "readiness_changed": before_score != after_score or before_class != after_class,
                "unresolved_blocker_count_after": unresolved_after,
                "unexplained_readiness_jump": (after_score != before_score or before_class != after_class) and not explained,
            },
        }
    )
    return output


def _why_changed(before_score: float, after_score: float, before_class: str, after_class: str, unresolved_after: int) -> list[str]:
    if before_score == after_score and before_class == after_class:
        return []
    reasons = []
    if before_score != after_score:
        reasons.append(f"Arbitrated readiness score moved from {before_score} to {after_score}.")
    if before_class != after_class:
        reasons.append(f"Classification moved from {before_class} to {after_class}.")
    if unresolved_after:
        reasons.append("Unresolved Tier 1 blockers remain, so any promotion remains capped by governance hardening.")
    return reasons


def _why_not_changed(before_score: float, after_score: float, before_class: str, after_class: str, unresolved_after: int) -> list[str]:
    if before_score != after_score or before_class != after_class:
        return []
    reasons = ["Readiness did not change because the reassessment inputs did not remove a blocking governance condition."]
    if unresolved_after:
        reasons.append("At least one Tier 1 blocker remains unresolved or lacks evidence-backed non-blocking disposition.")
    return reasons
