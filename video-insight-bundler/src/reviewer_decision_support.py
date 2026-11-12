"""Conservative decision-support notes for human reviewers."""

from __future__ import annotations

from intelligence_common import base_artifact, deterministic_id


def build_reviewer_decision_support(tier_1_blocker_disposition: dict, review_navigation_index: dict) -> dict:
    nav = {row.get("blocker_id"): row for row in review_navigation_index.get("navigation_items", [])}
    rows = []
    for blocker in tier_1_blocker_disposition.get("blocker_dispositions", []):
        blocker_id = blocker.get("blocker_id")
        family = blocker.get("blocker_family") or "unknown"
        navigation = nav.get(blocker_id, {})
        candidates = _candidates(family)
        rows.append(
            {
                "decision_support_id": deterministic_id("RDS", blocker_id, candidates, blocker.get("evidence_refs") or []),
                "blocker_id": blocker_id,
                "blocker_family": family,
                "likely_disposition_candidates": candidates,
                "rationale": _rationale(family),
                "minimum_evidence_needed": _minimum_evidence(family),
                "reviewer_caution_notes": [
                    "Do not treat proposed remediation as resolution.",
                    "Do not classify false positive without a concrete evidence reference.",
                    "Do not accept risk without reviewer rationale and evidence refs.",
                ],
                "possible_governance_consequences": _consequences(family),
                "reassessment_likely_to_change_readiness": bool(navigation) and navigation.get("governance_severity") == "hard_blocker",
                "evidence_refs": blocker.get("evidence_refs") or [],
                "navigation_ref": "workbench/review_navigation_index.json",
            }
        )
    output = base_artifact(method="deterministic_reviewer_decision_support_v1")
    output.update(
        {
            "reviewer_decision_support_id": deterministic_id("RDSSET", [(row["blocker_id"], row["likely_disposition_candidates"]) for row in rows]),
            "decision_support_items": rows,
            "summary": {"decision_support_item_count": len(rows), "non_applying": True},
        }
    )
    return output


def _candidates(family: str) -> list[str]:
    if "readiness" in family:
        return ["externally_reviewed", "resolved", "deferred"]
    if "pressure" in family or "counterfactual" in family:
        return ["externally_reviewed", "accepted_risk", "false_positive", "deferred"]
    return ["externally_reviewed", "resolved", "false_positive", "deferred"]


def _rationale(family: str) -> str:
    if "readiness" in family:
        return "Readiness blockers require evidence that the underlying release-readiness issue was reviewed and no longer blocks RC consideration."
    if "pressure" in family:
        return "Pressure blockers may be intentional rhetoric or real instability; the reviewer must inspect segment evidence before choosing a disposition."
    return "Disposition should follow the strongest evidence refs, not the existence of a proposed remediation."


def _minimum_evidence(family: str) -> list[str]:
    evidence = ["Specific evidence artifact reference", "Reviewer rationale", "Disposition value from allowed list"]
    if "readiness" in family:
        evidence.append("Release readiness or governance artifact reference showing why the cap can be removed")
    return evidence


def _consequences(family: str) -> list[str]:
    consequences = ["Evidence-backed non-blocking dispositions may remove a specific Tier 1 cap after reassessment."]
    consequences.append("Unresolved, deferred, proposed, or evidence-incomplete dispositions keep readiness capped.")
    if "readiness" in family:
        consequences.append("Readiness-family blockers are likely to affect rc_candidate eligibility directly.")
    return consequences
