"""Longitudinal operational trend analysis."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, stable_row_id, trend_rows_from_lineage


def build_operational_trend_analysis(outputs: dict) -> dict:
    entries = latest_lineage_entries(outputs)
    rows = []
    for metric in ["validation_timing_seconds", "dashboard_generation_seconds", "queue_generation_seconds", "operational_workload_units"]:
        rows.extend(trend_rows_from_lineage(entries, metric, "operational_trend", metric))
    artifact = phase41_artifact("deterministic_operational_trend_analysis_v1")
    artifact.update({"operational_trend_analysis_id": stable_row_id("OTR", [row["operational_trend_id"] for row in rows]), "trend_entries": rows, "summary": {"trend_entry_count": len(rows)}})
    return artifact


def render_operational_trend_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_trend_analysis") or {}).get("trend_entries") or []
    return render_longitudinal_page("Operational Trend Dashboard", "operational_trend_dashboard.html", rows, ["trend_type", "current_value", "previous_value", "delta", "trend_level"], "operational_trend_id", [("Trend entries", len(rows))])

