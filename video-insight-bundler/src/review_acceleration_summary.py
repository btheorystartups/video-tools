"""Deterministic review acceleration summary registry."""

from __future__ import annotations

from phase45_interaction_common import focus_specs, phase45_artifact, render_interaction_page, stable_row_id


def build_review_acceleration_registry(outputs: dict) -> dict:
    lens_count = (outputs.get("dashboard_lens_registry") or {}).get("summary", {}).get("active_lens_count", 0)
    route_count = (outputs.get("compact_routing_registry") or {}).get("summary", {}).get("compact_route_count", 0)
    repair_count = (outputs.get("continuity_repair_queue") or {}).get("summary", {}).get("continuity_repair_queue_count", 0)
    rows = []
    for focus, _keywords in focus_specs():
        rows.append(
            {
                "review_acceleration_id": stable_row_id("RACC", focus, lens_count, route_count, repair_count),
                "acceleration_scope": focus,
                "lens_available": lens_count > 0,
                "compact_routes_available": route_count > 0,
                "repair_queue_pressure": repair_count,
                "acceleration_summary": "Use lens filtering, priority traversal, and linked pathways to reduce dashboard hops.",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_review_acceleration_summary_v1")
    artifact.update({"review_acceleration_registry_id": stable_row_id("RACCREG", [row["review_acceleration_id"] for row in rows]), "review_acceleration_summaries": rows, "summary": {"review_acceleration_summary_count": len(rows)}})
    return artifact


def render_review_acceleration_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("review_acceleration_registry") or {}).get("review_acceleration_summaries") or []
    return render_interaction_page("Review Acceleration Dashboard", "review_acceleration_dashboard.html", rows, ["acceleration_scope", "lens_available", "compact_routes_available", "repair_queue_pressure", "acceleration_summary"], "review_acceleration_id", [("Acceleration summaries", len(rows))])
