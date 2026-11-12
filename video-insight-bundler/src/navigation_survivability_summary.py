"""Deterministic navigation survivability summaries."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_navigation_survivability_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 5)
        ids = source_ids(events)
        rows.append(
            {
                "navigation_survivability_id": stable_row_id("NSV", focus, ids),
                "focus": focus,
                "source_event_ids": ids,
                "drilldown_survivability": "complete" if ids else "review",
                "breadcrumb_survivability": "complete" if ids else "review",
                "deep_link_survivability": "complete" if ids else "review",
                "survivability_summary": f"{focus.title()} navigation remains drillable through {len(ids)} deterministic references.",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_navigation_survivability_summary_v1")
    artifact.update({"navigation_survivability_registry_id": stable_row_id("NSVREG", [row["navigation_survivability_id"] for row in rows]), "survivability_summaries": rows, "summary": {"survivability_summary_count": len(rows)}})
    return artifact


def render_navigation_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("navigation_survivability_registry") or {}).get("survivability_summaries") or []
    return render_wayfinding_page("Navigation Survivability Dashboard", "navigation_survivability_dashboard.html", rows, ["focus", "drilldown_survivability", "breadcrumb_survivability", "survivability_summary"], "navigation_survivability_id", [("Survivability summaries", len(rows))])
