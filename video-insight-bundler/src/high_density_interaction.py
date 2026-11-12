"""Deterministic high-density interaction affordances."""

from __future__ import annotations

from phase45_interaction_common import focus_specs, phase45_artifact, render_interaction_page, stable_row_id


def build_high_density_interaction_registry(outputs: dict) -> dict:
    rows = []
    sortable_count = (outputs.get("sortable_table_registry") or {}).get("summary", {}).get("sortable_table_count", 0)
    lens_count = (outputs.get("dashboard_lens_registry") or {}).get("summary", {}).get("dashboard_lens_count", 0)
    route_count = (outputs.get("compact_routing_registry") or {}).get("summary", {}).get("compact_route_count", 0)
    for focus, _keywords in focus_specs():
        rows.append(
            {
                "high_density_interaction_id": stable_row_id("HDI", focus, sortable_count, lens_count, route_count),
                "interaction_scope": focus,
                "sortable_table_available": sortable_count > 0,
                "filter_lens_available": lens_count > 0,
                "compact_route_available": route_count > 0,
                "density_status": "high_density_ready",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_high_density_interaction_v1")
    artifact.update({"high_density_interaction_registry_id": stable_row_id("HDIREG", [row["high_density_interaction_id"] for row in rows]), "high_density_interactions": rows, "summary": {"high_density_interaction_count": len(rows)}})
    return artifact


def render_high_density_interaction_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("high_density_interaction_registry") or {}).get("high_density_interactions") or []
    return render_interaction_page("High Density Interaction Dashboard", "high_density_interaction_dashboard.html", rows, ["interaction_scope", "sortable_table_available", "filter_lens_available", "compact_route_available", "density_status"], "high_density_interaction_id", [("Density entries", len(rows))])
