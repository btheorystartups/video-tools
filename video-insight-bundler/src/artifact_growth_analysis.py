"""Artifact growth analysis."""

from __future__ import annotations

from phase41_longitudinal_common import latest_lineage_entries, phase41_artifact, render_longitudinal_page, stable_row_id, trend_rows_from_lineage


def build_artifact_growth_analysis(outputs: dict) -> dict:
    rows = trend_rows_from_lineage(latest_lineage_entries(outputs), "artifact_total_count", "artifact_growth", "artifact_growth")
    artifact = phase41_artifact("deterministic_artifact_growth_analysis_v1")
    artifact.update({"artifact_growth_analysis_id": stable_row_id("AGROWREG", [row["artifact_growth_id"] for row in rows]), "artifact_growth_entries": rows, "summary": {"artifact_growth_entry_count": len(rows)}})
    return artifact


def render_artifact_growth_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("artifact_growth_analysis") or {}).get("artifact_growth_entries") or []
    return render_longitudinal_page("Artifact Growth Dashboard", "artifact_growth_dashboard.html", rows, ["current_value", "previous_value", "delta", "trend_level"], "artifact_growth_id", [("Artifact growth entries", len(rows))])

