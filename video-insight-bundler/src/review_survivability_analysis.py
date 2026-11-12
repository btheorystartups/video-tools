"""Review survivability trend analysis."""

from __future__ import annotations

from phase41_longitudinal_common import count_rows, phase41_artifact, render_longitudinal_page, risk_level, stable_row_id


def build_review_survivability_analysis(outputs: dict) -> dict:
    active = count_rows(outputs, "review_queue_registry", "queue_items")
    completed = count_rows(outputs, "review_completion_registry", "completion_items", "completed_items")
    score = round(completed / max(1, active + completed), 3)
    rows = [{"review_survivability_id": stable_row_id("RSURV", active, completed), "survivability_type": "review_queue_survivability", "active_review_count": active, "completed_review_count": completed, "survivability_score": score, "degradation_level": risk_level(1.0 - score), "human_review_required": True}]
    artifact = phase41_artifact("deterministic_review_survivability_analysis_v1")
    artifact.update({"review_survivability_analysis_id": stable_row_id("RSURVREG", [row["review_survivability_id"] for row in rows]), "survivability_entries": rows, "summary": {"survivability_entry_count": len(rows)}})
    return artifact


def render_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("review_survivability_analysis") or {}).get("survivability_entries") or []
    return render_longitudinal_page("Survivability Dashboard", "survivability_dashboard.html", rows, ["survivability_type", "active_review_count", "completed_review_count", "survivability_score", "degradation_level"], "review_survivability_id", [("Survivability entries", len(rows))])

