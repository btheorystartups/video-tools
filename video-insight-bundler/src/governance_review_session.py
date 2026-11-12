"""Deterministic human governance review session snapshots."""

from __future__ import annotations

from blocker_disposition import NON_BLOCKING_DISPOSITIONS, disposition_is_unresolved
from intelligence_common import base_artifact, deterministic_id


def build_governance_review_session(tier_1_blocker_disposition: dict, readiness_before: dict, readiness_after: dict | None = None, reviewer_name: str = "") -> dict:
    rows = tier_1_blocker_disposition.get("blocker_dispositions", [])
    reviewed = []
    decisions = []
    unresolved = []
    accepted_risks = []
    false_positive_claims = []
    external_refs = []
    reviewed_artifacts = sorted(
        {
            "governance/tier_1_blocker_disposition.json",
            "governance/blocker_analysis.json",
            "workbench/compressed_review_queue.json",
            "workbench/tier_1_review_packet.json",
        }
    )
    for row in rows:
        reviewed.append(row.get("blocker_id"))
        evidence = row.get("decision_evidence_refs") or []
        decision = row.get("disposition") or "proposed"
        if decision != "proposed" or evidence:
            decisions.append(
                {
                    "blocker_id": row.get("blocker_id"),
                    "disposition": decision,
                    "decision_evidence_refs": evidence,
                    "reviewer_confidence": row.get("reviewer_confidence", "unspecified"),
                    "rationale": row.get("decision_rationale", ""),
                }
            )
        if disposition_is_unresolved(row):
            unresolved.append(row.get("blocker_id"))
        if decision == "accepted_risk":
            accepted_risks.append({"blocker_id": row.get("blocker_id"), "evidence_refs": evidence})
        if decision == "false_positive":
            false_positive_claims.append({"blocker_id": row.get("blocker_id"), "evidence_refs": evidence})
        if decision == "externally_reviewed":
            external_refs.append({"blocker_id": row.get("blocker_id"), "evidence_refs": evidence})

    after = readiness_after or readiness_before
    before_score = readiness_before.get("arbitrated_readiness_score")
    after_score = after.get("arbitrated_readiness_score")
    output = base_artifact(method="deterministic_governance_review_session_v1")
    output.update(
        {
            "session_id": deterministic_id("GREVSESS", tier_1_blocker_disposition.get("tier_1_blocker_disposition_id"), [(row.get("blocker_id"), row.get("disposition"), row.get("decision_evidence_refs") or []) for row in rows]),
            "session_timestamp": output["generated_at_utc"],
            "reviewer_name": reviewer_name,
            "reviewed_blockers": reviewed,
            "reviewed_artifacts": reviewed_artifacts,
            "decisions_applied": decisions,
            "unresolved_items": unresolved,
            "accepted_risks": accepted_risks,
            "false_positive_claims": false_positive_claims,
            "external_review_refs": external_refs,
            "reviewer_confidence": _confidence(decisions),
            "reassessment_triggered": bool(decisions),
            "readiness_before": {"classification": readiness_before.get("classification"), "score": before_score},
            "readiness_after": {"classification": after.get("classification"), "score": after_score},
            "readiness_delta": {
                "score_delta": round((after_score or 0.0) - (before_score or 0.0), 3),
                "classification_before": readiness_before.get("classification"),
                "classification_after": after.get("classification"),
            },
            "governance_notes": [
                "No reviewer decisions were auto-created." if not decisions else "Reviewer decisions were captured from existing disposition evidence.",
                "Non-blocking dispositions require evidence and remain review-only.",
            ],
            "summary": {
                "reviewed_blocker_count": len(reviewed),
                "decision_count": len(decisions),
                "unresolved_count": len(unresolved),
                "accepted_risk_count": len(accepted_risks),
                "false_positive_claim_count": len(false_positive_claims),
            },
        }
    )
    return output


def build_reviewer_session_summary(session: dict) -> dict:
    output = base_artifact(method="deterministic_reviewer_session_summary_v1")
    output.update(
        {
            "reviewer_session_summary_id": deterministic_id("GREVSESSSUM", session.get("session_id"), session.get("summary")),
            "session_ref": "governance/governance_review_session.json",
            "reviewer_name": session.get("reviewer_name"),
            "reviewed_blocker_count": (session.get("summary") or {}).get("reviewed_blocker_count", 0),
            "decision_count": (session.get("summary") or {}).get("decision_count", 0),
            "unresolved_count": (session.get("summary") or {}).get("unresolved_count", 0),
            "readiness_delta": session.get("readiness_delta") or {},
            "next_review_step": "Review unresolved Tier 1 blockers and attach evidence-backed decisions before reassessment can lift caps.",
            "summary": session.get("summary") or {},
        }
    )
    return output


def _confidence(decisions: list[dict]) -> str:
    if not decisions:
        return "unspecified"
    values = {row.get("reviewer_confidence") for row in decisions}
    if "low" in values:
        return "low"
    if "medium" in values:
        return "medium"
    if values <= {"high"}:
        return "high"
    return "mixed"
