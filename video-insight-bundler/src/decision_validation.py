"""Validate local reviewer decision intake before governance reassessment."""

from __future__ import annotations

from datetime import date

from blocker_disposition import ALLOWED_DISPOSITIONS, NON_BLOCKING_DISPOSITIONS
from intelligence_common import base_artifact, deterministic_id


CONFIDENCE_VALUES = {"low", "medium", "high"}
CLEARING_DISPOSITIONS = set(NON_BLOCKING_DISPOSITIONS)


def validate_reviewer_decisions(reviewer_decisions: dict, tier_1_blocker_disposition: dict) -> dict:
    blockers = {row.get("blocker_id"): row for row in tier_1_blocker_disposition.get("blocker_dispositions", [])}
    decisions = reviewer_decisions.get("decisions") or []
    validated = []
    rejected = []
    for raw in decisions:
        decision = _normalize_decision(raw)
        reasons, missing, invalid = _validate_one(decision, blockers)
        if reasons:
            rejected.append(
                {
                    "decision_id": decision.get("decision_id") or "",
                    "blocker_id": decision.get("blocker_id") or "",
                    "rejection_reasons": reasons,
                    "missing_fields": missing,
                    "invalid_fields": invalid,
                    "suggested_fix": _suggest_fix(missing, invalid),
                    "source_decision": decision,
                }
            )
        else:
            blocker = blockers[decision["blocker_id"]]
            validated.append(
                {
                    **decision,
                    "decision_id": decision.get("decision_id") or deterministic_id("HDEC", decision.get("blocker_id"), decision.get("disposition"), decision.get("reviewer_name"), decision.get("review_date")),
                    "source_blocker_ref": "governance/tier_1_blocker_disposition.json",
                    "source_reviewer_file_ref": "review_input/reviewer_decisions.json",
                    "validation_status": "valid",
                    "clears_blocker_candidate": decision.get("disposition") in CLEARING_DISPOSITIONS,
                    "blocker_evidence_refs": blocker.get("evidence_refs") or [],
                }
            )

    valid_artifact = base_artifact(method="deterministic_validated_human_decisions_v1")
    valid_artifact.update(
        {
            "validated_human_decisions_id": deterministic_id("VHD", [(row.get("decision_id"), row.get("blocker_id"), row.get("disposition")) for row in validated]),
            "source_reviewer_decisions_ref": "review_input/reviewer_decisions.json",
            "source_tier_1_disposition_ref": "governance/tier_1_blocker_disposition.json",
            "allowed_dispositions": ALLOWED_DISPOSITIONS,
            "validated_decisions": sorted(validated, key=lambda row: (row.get("blocker_id") or "", row.get("decision_id") or "")),
            "summary": {
                "valid_decision_count": len(validated),
                "clearing_decision_count": sum(1 for row in validated if row.get("clears_blocker_candidate")),
                "reviewer_decisions_present": bool(decisions),
            },
        }
    )
    rejected_artifact = base_artifact(method="deterministic_rejected_human_decisions_v1")
    rejected_artifact.update(
        {
            "rejected_human_decisions_id": deterministic_id("RHD", [(row.get("decision_id"), row.get("blocker_id"), row.get("rejection_reasons")) for row in rejected]),
            "source_reviewer_decisions_ref": "review_input/reviewer_decisions.json",
            "rejected_decisions": sorted(rejected, key=lambda row: (row.get("blocker_id") or "", row.get("decision_id") or "")),
            "summary": {"rejected_decision_count": len(rejected), "reviewer_decisions_present": bool(decisions)},
        }
    )
    return {"validated_human_decisions": valid_artifact, "rejected_human_decisions": rejected_artifact}


def _normalize_decision(raw: dict) -> dict:
    evidence_refs = raw.get("evidence_refs") or []
    if isinstance(evidence_refs, str):
        evidence_refs = [evidence_refs]
    return {
        "decision_id": str(raw.get("decision_id") or "").strip(),
        "blocker_id": str(raw.get("blocker_id") or "").strip(),
        "source_compressed_item_id": str(raw.get("source_compressed_item_id") or "").strip(),
        "disposition": str(raw.get("disposition") or "").strip(),
        "reviewer_name": str(raw.get("reviewer_name") or "").strip(),
        "review_date": str(raw.get("review_date") or "").strip(),
        "decision_confidence": raw.get("decision_confidence"),
        "evidence_note": str(raw.get("evidence_note") or "").strip(),
        "evidence_refs": sorted({str(ref).strip() for ref in evidence_refs if str(ref).strip()}),
        "rationale": str(raw.get("rationale") or "").strip(),
        "follow_up_required": bool(raw.get("follow_up_required", False)),
        "external_review_reference": str(raw.get("external_review_reference") or "").strip(),
        "accepted_risk_reason": str(raw.get("accepted_risk_reason") or "").strip(),
        "false_positive_reason": str(raw.get("false_positive_reason") or "").strip(),
        "resolved_reason": str(raw.get("resolved_reason") or "").strip(),
        "deferred_reason": str(raw.get("deferred_reason") or "").strip(),
        "governance_notes": str(raw.get("governance_notes") or "").strip(),
    }


def _validate_one(decision: dict, blockers: dict) -> tuple[list[str], list[str], list[str]]:
    reasons: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    for field in ["blocker_id", "source_compressed_item_id", "disposition", "reviewer_name", "review_date", "decision_confidence", "rationale", "evidence_note"]:
        if decision.get(field) in (None, ""):
            missing.append(field)
    blocker = blockers.get(decision.get("blocker_id"))
    if not blocker and decision.get("blocker_id"):
        invalid.append("blocker_id")
        reasons.append("blocker_id does not exist in current Tier 1 disposition artifacts.")
    if blocker and decision.get("source_compressed_item_id") != blocker.get("source_compressed_item_id"):
        invalid.append("source_compressed_item_id")
        reasons.append("source_compressed_item_id does not match the blocker.")
    if decision.get("disposition") and decision.get("disposition") not in ALLOWED_DISPOSITIONS:
        invalid.append("disposition")
        reasons.append("disposition is not allowed.")
    if decision.get("review_date") and not _valid_iso_date(decision.get("review_date")):
        invalid.append("review_date")
        reasons.append("review_date must be a valid ISO date.")
    if not _valid_confidence(decision.get("decision_confidence")):
        invalid.append("decision_confidence")
        reasons.append("decision_confidence must be low, medium, high, or a number from 0 through 1.")
    disposition = decision.get("disposition")
    if disposition in CLEARING_DISPOSITIONS and not decision.get("evidence_refs"):
        missing.append("evidence_refs")
        reasons.append("clearing dispositions require evidence_refs.")
    if disposition == "accepted_risk" and not decision.get("accepted_risk_reason"):
        missing.append("accepted_risk_reason")
        reasons.append("accepted_risk requires accepted_risk_reason.")
    if disposition == "false_positive" and not decision.get("false_positive_reason"):
        missing.append("false_positive_reason")
        reasons.append("false_positive requires false_positive_reason.")
    if disposition == "resolved" and not decision.get("resolved_reason"):
        missing.append("resolved_reason")
        reasons.append("resolved requires resolved_reason.")
    if disposition == "externally_reviewed" and not (decision.get("external_review_reference") or decision.get("evidence_note")):
        missing.append("external_review_reference")
        reasons.append("externally_reviewed requires external_review_reference or evidence_note.")
    if disposition == "deferred" and not decision.get("deferred_reason"):
        missing.append("deferred_reason")
        reasons.append("deferred requires deferred_reason.")
    if missing:
        reasons.extend(f"missing required field: {field}" for field in sorted(set(missing)))
    return sorted(set(reasons)), sorted(set(missing)), sorted(set(invalid))


def _valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _valid_confidence(value) -> bool:
    if isinstance(value, str):
        value = value.strip().lower()
        if value in CONFIDENCE_VALUES:
            return True
        try:
            value = float(value)
        except ValueError:
            return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return 0 <= float(value) <= 1
    return False


def _suggest_fix(missing: list[str], invalid: list[str]) -> str:
    parts = []
    if missing:
        parts.append("Populate: " + ", ".join(sorted(set(missing))) + ".")
    if invalid:
        parts.append("Correct: " + ", ".join(sorted(set(invalid))) + ".")
    return " ".join(parts) or "Review decision against reviewer_decisions.schema.json."
