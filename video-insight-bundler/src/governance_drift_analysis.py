"""Longitudinal governance drift visibility."""

from __future__ import annotations

from phase41_longitudinal_common import ambiguity_count, escalation_count, governance_pressure, phase41_artifact, render_longitudinal_page, risk_level, stable_row_id


def build_governance_drift_analysis(outputs: dict) -> dict:
    specs = [
        ("blocker_growth", governance_pressure(outputs)),
        ("escalation_accumulation", escalation_count(outputs)),
        ("unresolved_ambiguity_growth", ambiguity_count(outputs)),
        ("governance_review_pressure", governance_pressure(outputs) + escalation_count(outputs)),
    ]
    max_value = max([value for _, value in specs] or [1], default=1)
    rows = [
        {
            "governance_drift_id": stable_row_id("GDRIFT", drift_type, value),
            "drift_type": drift_type,
            "current_count": value,
            "pressure_score": round(value / max(1, max_value), 3),
            "drift_level": risk_level(value / max(1, max_value)),
            "human_review_required": True,
        }
        for drift_type, value in specs
    ]
    artifact = phase41_artifact("deterministic_governance_drift_analysis_v1")
    artifact.update({"governance_drift_analysis_id": stable_row_id("GDRIFTREG", [row["governance_drift_id"] for row in rows]), "governance_drift_entries": rows, "summary": {"governance_drift_entry_count": len(rows), "high_drift_count": sum(1 for row in rows if row["drift_level"] == "high")}})
    return artifact


def render_governance_drift_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("governance_drift_analysis") or {}).get("governance_drift_entries") or []
    return render_longitudinal_page("Governance Drift Dashboard", "governance_drift_dashboard.html", rows, ["drift_type", "current_count", "pressure_score", "drift_level"], "governance_drift_id", [("Drift entries", len(rows))])

