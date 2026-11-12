"""Queue growth trend analysis."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, stable_row_id, trend_rows_from_lineage


def build_queue_growth_analysis(outputs: dict) -> dict:
    rows = trend_rows_from_lineage(latest_lineage_entries(outputs), "queue_total_count", "queue_growth", "queue_growth")
    artifact = phase41_artifact("deterministic_queue_growth_analysis_v1")
    artifact.update({"queue_growth_analysis_id": stable_row_id("QGROWREG", [row["queue_growth_id"] for row in rows]), "queue_growth_entries": rows, "summary": {"queue_growth_entry_count": len(rows)}})
    return artifact


def render_queue_growth_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("queue_growth_analysis") or {}).get("queue_growth_entries") or []
    return render_longitudinal_page("Queue Growth Dashboard", "queue_growth_dashboard.html", rows, ["current_value", "previous_value", "delta", "trend_level"], "queue_growth_id", [("Queue growth entries", len(rows))])

