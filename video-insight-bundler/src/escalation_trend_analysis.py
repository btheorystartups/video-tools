"""Escalation trend analysis."""

from __future__ import annotations

from phase41_longitudinal_common import escalation_count, phase41_artifact, render_longitudinal_page, risk_level, stable_row_id


def build_escalation_trend_analysis(outputs: dict) -> dict:
    count = escalation_count(outputs)
    rows = [{"escalation_trend_id": stable_row_id("ETREND", count), "trend_type": "escalation_accumulation", "current_count": count, "trend_level": risk_level(min(1.0, count / 10)), "human_review_required": True}]
    artifact = phase41_artifact("deterministic_escalation_trend_analysis_v1")
    artifact.update({"escalation_trend_analysis_id": stable_row_id("ETRENDREG", [row["escalation_trend_id"] for row in rows]), "escalation_trend_entries": rows, "summary": {"escalation_trend_entry_count": len(rows)}})
    return artifact


def render_escalation_trend_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("escalation_trend_analysis") or {}).get("escalation_trend_entries") or []
    return render_longitudinal_page("Escalation Trend Dashboard", "escalation_trend_dashboard.html", rows, ["trend_type", "current_count", "trend_level"], "escalation_trend_id", [("Escalation trends", len(rows))])

