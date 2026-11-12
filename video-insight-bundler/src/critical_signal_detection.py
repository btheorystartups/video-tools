"""Detect high-signal review concerns in portable exports."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def detect_critical_signals(validation: dict, governance: dict | None, findings: dict, reduction: dict | None = None) -> dict:
    rows = []
    if validation.get("broken_link_count", 0):
        rows.append(_signal("portable_broken_links", "critical", validation.get("broken_link_count"), "Offline navigation has broken links."))
    if validation.get("missing_asset_count", 0):
        rows.append(_signal("portable_missing_assets", "critical", validation.get("missing_asset_count"), "Offline dashboards reference missing assets."))
    consistency = ((governance or {}).get("review_coherence_report") or {}).get("summary", {})
    if consistency.get("low_value_dashboard_count", 0):
        rows.append(_signal("low_value_dashboard_load", "medium", consistency.get("low_value_dashboard_count"), "Low-value dashboards may distract reviewers."))
    for finding in (findings.get("findings") or [])[:5]:
        if finding.get("severity") in {"critical", "high"}:
            rows.append(
                {
                    "signal_id": deterministic_id("SIG", finding.get("finding_id")),
                    "signal_type": "finding",
                    "severity": finding.get("severity"),
                    "strength": finding.get("review_priority"),
                    "summary": finding.get("summary"),
                    "supporting_artifacts": finding.get("supporting_artifacts") or [],
                }
            )
    if reduction and reduction.get("summary", {}).get("navigation_reduction_ratio", 0) > 0.25:
        rows.append(_signal("artifact_reduction_effective", "low", reduction["summary"]["navigation_reduction_ratio"], "Navigation was meaningfully compressed while preserving audit artifacts."))
    return {
        "analysis_status": "complete",
        "method": "critical_signal_detection_v73",
        "generated_at_utc": utc_now_iso(),
        "critical_signals": rows,
        "summary": {"signal_count": len(rows), "critical_signal_count": sum(1 for row in rows if row.get("severity") == "critical")},
    }


def _signal(signal_type: str, severity: str, strength: object, summary: str) -> dict:
    return {
        "signal_id": deterministic_id("SIG", signal_type, strength),
        "signal_type": signal_type,
        "severity": severity,
        "strength": strength,
        "summary": summary,
        "supporting_artifacts": ["portable_package_validation_report.json"],
    }
