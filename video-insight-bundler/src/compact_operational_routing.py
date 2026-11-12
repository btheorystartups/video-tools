"""Deterministic compact operational routing registry."""

from __future__ import annotations

from phase45_interaction_common import phase45_artifact, render_interaction_page, route_rows, stable_row_id


def build_compact_routing_registry(outputs: dict) -> dict:
    rows = route_rows()
    artifact = phase45_artifact("deterministic_compact_operational_routing_v1")
    artifact.update({"compact_routing_registry_id": stable_row_id("CRTEG", [row["route_id"] for row in rows]), "compact_routes": rows, "summary": {"compact_route_count": len(rows), "relative_route_count": len([row for row in rows if not row["dashboard_href"].startswith("http")])}})
    return artifact


def render_compact_routing_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("compact_routing_registry") or {}).get("compact_routes") or []
    return render_interaction_page("Compact Routing Dashboard", "compact_routing_dashboard.html", rows, ["route_type", "dashboard_href", "next_dashboard_href", "route_status"], "route_id", [("Routes", len(rows))])
