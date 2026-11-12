"""Deterministic layered recall drilldowns."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_layered_recall_drilldown(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 6)
        rows.append(
            {
                "layered_recall_drilldown_id": stable_row_id("LRD", focus, source_ids(events)),
                "focus": focus,
                "top_level_summary": f"{focus.title()} recall contains {len(events)} deterministic source events.",
                "mid_level_continuity_groups": [f"{focus}_continuity_group"],
                "detailed_operational_state_ids": source_ids(events),
                "escalation_drilldown_available": focus == "escalation",
                "governance_drilldown_available": focus == "governance",
                "survivability_drilldown_available": focus == "survivability",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_layered_recall_drilldown_v1")
    artifact.update({"layered_recall_drilldown_id": stable_row_id("LRDREG", [row["layered_recall_drilldown_id"] for row in rows]), "drilldowns": rows, "summary": {"drilldown_count": len(rows)}})
    return artifact


def render_layered_recall_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("layered_recall_drilldown") or {}).get("drilldowns") or []
    return render_wayfinding_page("Layered Recall Dashboard", "layered_recall_dashboard.html", rows, ["focus", "top_level_summary", "detailed_operational_state_ids"], "layered_recall_drilldown_id", [("Drilldowns", len(rows))])
