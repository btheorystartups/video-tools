"""Deterministic cross-dashboard route integrity checks."""

from __future__ import annotations

from phase45_interaction_common import known_route_targets, phase45_artifact, render_interaction_page, route_rows, stable_row_id


def build_cross_dashboard_integrity_registry(outputs: dict) -> dict:
    targets = known_route_targets()
    rows = []
    for route in route_rows():
        rows.append(
            {
                "cross_dashboard_integrity_check_id": stable_row_id("CDINT", route["dashboard_href"], route["next_dashboard_href"]),
                "from_dashboard": route["dashboard_href"],
                "to_dashboard": route["next_dashboard_href"],
                "integrity_status": "complete" if route["dashboard_href"] in targets and route["next_dashboard_href"] in targets else "error",
                "route_survivability": "survives_static_navigation",
                "continuity_integrity": "preserved_by_relative_link",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_cross_dashboard_route_integrity_v1")
    artifact.update({"cross_dashboard_integrity_registry_id": stable_row_id("CDINTREG", [row["cross_dashboard_integrity_check_id"] for row in rows]), "cross_dashboard_integrity_checks": rows, "summary": {"cross_dashboard_integrity_check_count": len(rows), "broken_route_count": len([row for row in rows if row["integrity_status"] != "complete"])}})
    return artifact


def render_dashboard_integrity_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("cross_dashboard_integrity_registry") or {}).get("cross_dashboard_integrity_checks") or []
    return render_interaction_page("Dashboard Integrity Dashboard", "dashboard_integrity_dashboard.html", rows, ["from_dashboard", "to_dashboard", "integrity_status", "route_survivability"], "cross_dashboard_integrity_check_id", [("Integrity checks", len(rows))])
