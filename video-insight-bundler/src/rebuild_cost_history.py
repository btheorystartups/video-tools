"""Historical rebuild-cost analysis."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, stable_row_id, trend_rows_from_lineage


def build_rebuild_cost_history(outputs: dict) -> dict:
    rows = trend_rows_from_lineage(latest_lineage_entries(outputs), "rebuild_timing_seconds", "rebuild_cost_history", "rebuild_cost_history")
    artifact = phase41_artifact("deterministic_rebuild_cost_history_v1")
    artifact.update({"rebuild_cost_history_id": stable_row_id("RCHISTREG", [row["rebuild_cost_history_id"] for row in rows]), "rebuild_cost_entries": rows, "summary": {"rebuild_cost_entry_count": len(rows)}})
    return artifact


def render_rebuild_cost_history_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("rebuild_cost_history") or {}).get("rebuild_cost_entries") or []
    return render_longitudinal_page("Rebuild Cost History Dashboard", "rebuild_cost_history_dashboard.html", rows, ["current_value", "previous_value", "delta", "trend_level"], "rebuild_cost_history_id", [("Rebuild entries", len(rows))])

