"""Cross-session operational analytics."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, stable_row_id, trend_rows_from_lineage


def build_cross_session_analytics(outputs: dict) -> dict:
    entries = latest_lineage_entries(outputs)
    rows = []
    for metric, label in [
        ("queue_total_count", "queue_survivability_change"),
        ("operational_workload_units", "operational_workload_change"),
        ("artifact_total_count", "artifact_growth_change"),
        ("rebuild_timing_seconds", "rebuild_cost_change"),
    ]:
        rows.extend(trend_rows_from_lineage(entries, metric, "cross_session_analytics", label))
    artifact = phase41_artifact("deterministic_cross_session_analytics_v1")
    artifact.update({"cross_session_analytics_id": stable_row_id("CSA", [row["cross_session_analytics_id"] for row in rows]), "session_analytics": rows, "summary": {"session_analytics_count": len(rows), "lineage_entry_count": len(entries)}})
    return artifact


def render_cross_session_analytics_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("cross_session_analytics") or {}).get("session_analytics") or []
    return render_longitudinal_page("Cross-Session Analytics Dashboard", "cross_session_analytics_dashboard.html", rows, ["trend_type", "metric", "current_value", "delta", "trend_level"], "cross_session_analytics_id", [("Analytics", len(rows))])

