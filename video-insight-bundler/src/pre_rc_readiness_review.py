"""Pre-RC readiness review that keeps beta classification."""

from __future__ import annotations

from pathlib import Path

from known_limitations_registry import build_known_limitations_registry
from manual_review_requirements import build_manual_review_requirements
from operational_risk_registry import build_operational_risk_registry
from stability import utc_now_iso, write_json


def build_pre_rc_readiness_review(package_root: Path, validation: dict, consistency: dict | None, reduction: dict | None, synthesis: dict | None) -> dict:
    risks = build_operational_risk_registry(validation, consistency, reduction)
    limitations = build_known_limitations_registry()
    manual = build_manual_review_requirements(risks)
    blockers = [row for row in risks.get("risks", []) if row.get("disposition") in {"must_fix_before_rc", "should_fix_before_rc"}]
    report = {
        "analysis_status": "complete",
        "method": "pre_rc_readiness_review_v79",
        "generated_at_utc": utc_now_iso(),
        "classification": "operational beta+ / internal beta_plus",
        "rc_promotion_recommended": False,
        "must_fix_before_rc": [row for row in blockers if row.get("disposition") == "must_fix_before_rc"],
        "should_fix_before_rc": [row for row in blockers if row.get("disposition") == "should_fix_before_rc"],
        "future_enhancement": [{"summary": "Screenshot-based dashboard review and richer natural-language synthesis calibration."}],
        "known_beta_limitation": limitations.get("limitations", []),
        "summary": {
            "remaining_beta_blocker_count": len(blockers),
            "must_fix_before_rc_count": len([row for row in blockers if row.get("disposition") == "must_fix_before_rc"]),
            "rc_promotion_recommended": False,
        },
    }
    remaining = {"analysis_status": "complete", "method": "remaining_beta_blockers_v79", "generated_at_utc": utc_now_iso(), "blockers": blockers, "summary": {"blocker_count": len(blockers)}}
    for rel, payload in [
        ("pre_rc_readiness_report.json", report),
        ("operational_risk_registry.json", risks),
        ("known_limitations_registry.json", limitations),
        ("manual_review_requirements.json", manual),
        ("remaining_beta_blockers.json", remaining),
    ]:
        write_json(package_root / rel, payload)
        write_json(package_root / "review" / rel, payload)
    return {"pre_rc_readiness_report": report, "operational_risk_registry": risks, "known_limitations_registry": limitations, "manual_review_requirements": manual, "remaining_beta_blockers": remaining}
