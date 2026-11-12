"""Operational risk registry for beta portable exports."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def build_operational_risk_registry(validation: dict, consistency: dict | None, reduction: dict | None) -> dict:
    risks = []
    if validation.get("broken_link_count", 0) or validation.get("missing_asset_count", 0):
        risks.append(_risk("portable_integrity", "must_fix_before_rc", "Portable validation issues remain."))
    if (consistency or {}).get("summary", {}).get("issue_count", 0):
        risks.append(_risk("dashboard_consistency", "should_fix_before_rc", "Dashboard consistency validation found layout or metadata issues."))
    if (reduction or {}).get("summary", {}).get("pages_after", 0) > 80:
        risks.append(_risk("reviewer_overload", "should_fix_before_rc", "Export still exposes a large dashboard surface."))
    risks.append(_risk("human_synthesis_review", "known_beta_limitation", "Deterministic synthesis requires human confirmation before external release."))
    return {"analysis_status": "complete", "method": "operational_risk_registry_v79", "generated_at_utc": utc_now_iso(), "risks": risks, "summary": {"risk_count": len(risks), "must_fix_before_rc_count": sum(1 for row in risks if row["disposition"] == "must_fix_before_rc")}}


def _risk(kind: str, disposition: str, summary: str) -> dict:
    return {"risk_id": deterministic_id("ORISK", kind, disposition), "risk_type": kind, "disposition": disposition, "summary": summary}
