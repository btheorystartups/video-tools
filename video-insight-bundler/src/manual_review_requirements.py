"""Manual review requirements before RC consideration."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def build_manual_review_requirements(risks: dict) -> dict:
    requirements = [
        ("executive_packet_readthrough", "Confirm top findings are concise and non-generic."),
        ("dashboard_coherence_spotcheck", "Spot-check core dashboards for layout consistency and useful review guidance."),
        ("audit_traceability_spotcheck", "Verify hidden/aggregated artifacts remain reachable for audit use."),
    ]
    if risks.get("summary", {}).get("must_fix_before_rc_count", 0):
        requirements.append(("blocker_resolution", "Resolve must-fix operational risks before RC promotion."))
    return {"analysis_status": "complete", "method": "manual_review_requirements_v79", "generated_at_utc": utc_now_iso(), "requirements": [{"requirement_id": deterministic_id("MREV", key), "requirement_type": key, "required_before_rc": True, "summary": text} for key, text in requirements], "summary": {"requirement_count": len(requirements)}}
