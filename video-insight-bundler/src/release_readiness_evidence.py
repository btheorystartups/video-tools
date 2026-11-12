"""Release-readiness evidence without promoting classification."""

from __future__ import annotations

from pathlib import Path

from stability import utc_now_iso, write_json


def build_release_readiness_evidence(package_root: Path, *, validation: dict | None = None, ci_smoke: dict | None = None, benchmark: dict | None = None) -> dict:
    blockers = []
    validation = validation or {}
    if not validation.get("validation_passed"):
        blockers.append({"blocker_id": "validation_not_passing", "severity": "high", "status": "open"})
    if (validation.get("broken_link_count") or 0) > 0:
        blockers.append({"blocker_id": "broken_links_present", "severity": "high", "status": "open"})
    if (validation.get("missing_asset_count") or 0) > 0:
        blockers.append({"blocker_id": "missing_assets_present", "severity": "high", "status": "open"})
    evidence = {
        "analysis_status": "complete",
        "method": "portable_release_readiness_evidence_v72",
        "generated_at_utc": utc_now_iso(),
        "classification": "operational beta+ / internal beta_plus",
        "rc_promotion_recommended": False,
        "rc_promotion_status": "not recommended yet",
        "validation_summary": validation.get("summary", {}),
        "ci_smoke_summary": (ci_smoke or {}).get("summary", {}),
        "benchmark_summary": (benchmark or {}).get("summary", {}),
        "summary": {"blocker_count": len(blockers), "evidence_ready_for_future_rc_review": len(blockers) == 0},
    }
    blocker_registry = {
        "analysis_status": "complete",
        "method": "rc_blocker_evidence_registry_v72",
        "generated_at_utc": utc_now_iso(),
        "classification": "operational beta+ / internal beta_plus",
        "rc_promotion_recommended": False,
        "blockers": blockers,
        "summary": {"open_blocker_count": len(blockers)},
    }
    write_json(package_root / "portable_release_readiness_evidence.json", evidence)
    write_json(package_root / "rc_blocker_evidence_registry.json", blocker_registry)
    write_json(package_root / "validation" / "portable_release_readiness_evidence.json", evidence)
    write_json(package_root / "validation" / "rc_blocker_evidence_registry.json", blocker_registry)
    return evidence
