"""Deterministic longitudinal continuity panels."""

from __future__ import annotations

from phase43_recall_common import RECALL_LENSES, events_for_focus, phase43_artifact, render_recall_page, source_ids, stable_row_id


def build_longitudinal_continuity_registry(outputs: dict) -> dict:
    panels = []
    for focus, _keywords in RECALL_LENSES:
        events = events_for_focus(outputs, focus, 5)
        panels.append(
            {
                "longitudinal_continuity_panel_id": stable_row_id("LCP", focus, source_ids(events)),
                "panel_type": f"{focus}_continuity",
                "focus": focus,
                "source_event_ids": source_ids(events),
                "visible_event_count": len(events),
                "panel_summary": f"{focus.title()} continuity panel links {len(events)} historical events.",
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_longitudinal_continuity_panel_v1")
    artifact.update({"longitudinal_continuity_registry_id": stable_row_id("LCPREG", [row["longitudinal_continuity_panel_id"] for row in panels]), "continuity_panels": panels, "summary": {"continuity_panel_count": len(panels)}})
    return artifact


def render_continuity_panel_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("longitudinal_continuity_registry") or {}).get("continuity_panels") or []
    return render_recall_page("Continuity Panel Dashboard", "continuity_panel_dashboard.html", rows, ["panel_type", "visible_event_count", "panel_summary"], "longitudinal_continuity_panel_id", [("Continuity panels", len(rows))])
