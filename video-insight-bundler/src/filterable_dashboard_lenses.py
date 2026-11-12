"""Deterministic filterable dashboard lens registry."""

from __future__ import annotations

from phase45_interaction_common import focus_events, focus_specs, phase45_artifact, render_interaction_page, source_ids, stable_row_id


def build_dashboard_lens_registry(outputs: dict) -> dict:
    rows = []
    for focus, keywords in focus_specs():
        events = focus_events(outputs, focus, 16)
        ids = source_ids(events)
        rows.append(
            {
                "dashboard_lens_id": stable_row_id("DLENS", focus, ids),
                "lens_type": focus,
                "lens_keywords": keywords,
                "matching_event_count": len(ids),
                "source_event_ids": ids,
                "filter_status": "available" if ids else "empty",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_filterable_dashboard_lenses_v1")
    artifact.update({"dashboard_lens_registry_id": stable_row_id("DLENSREG", [row["dashboard_lens_id"] for row in rows]), "dashboard_lenses": rows, "summary": {"dashboard_lens_count": len(rows), "active_lens_count": len([row for row in rows if row["matching_event_count"]])}})
    return artifact


def render_dashboard_lenses_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("dashboard_lens_registry") or {}).get("dashboard_lenses") or []
    return render_interaction_page("Dashboard Lenses Dashboard", "dashboard_lenses_dashboard.html", rows, ["lens_type", "matching_event_count", "filter_status", "source_event_ids"], "dashboard_lens_id", [("Lenses", len(rows))], [row.get("lens_type") for row in rows])
