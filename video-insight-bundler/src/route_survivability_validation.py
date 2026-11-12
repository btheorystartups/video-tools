"""Deterministic route survivability validation."""

from __future__ import annotations

from phase45_interaction_common import known_route_targets, phase45_artifact, render_interaction_page, route_rows, stable_row_id


def build_route_survivability_registry(outputs: dict) -> dict:
    targets = known_route_targets()
    deep_links = (outputs.get("contextual_deep_link_registry") or {}).get("deep_links") or []
    rows = []
    for route in route_rows():
        next_ok = route["next_dashboard_href"] in targets
        rows.append(
            {
                "route_survivability_check_id": stable_row_id("RSV", route["route_id"], next_ok),
                "route_id": route["route_id"],
                "check": "relative_static_route_survives",
                "status": "complete" if next_ok else "error",
                "dashboard_href": route["dashboard_href"],
                "broken_deep_link_count": len([link for link in deep_links if not str(link.get("target_fragment") or "").startswith("#")]),
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_route_survivability_validation_v1")
    artifact.update({"route_survivability_registry_id": stable_row_id("RSVREG", [row["route_survivability_check_id"] for row in rows]), "route_survivability_checks": rows, "summary": {"route_survivability_check_count": len(rows), "route_issue_count": len([row for row in rows if row["status"] != "complete"])}})
    return artifact


def render_route_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("route_survivability_registry") or {}).get("route_survivability_checks") or []
    return render_interaction_page("Route Survivability Dashboard", "route_survivability_dashboard.html", rows, ["route_id", "check", "status", "dashboard_href", "broken_deep_link_count"], "route_survivability_check_id", [("Route checks", len(rows))])
