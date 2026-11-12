"""Deterministic focus survivability routing."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, resilience_routes, stable_row_id


def build_focus_survivability_registry(outputs: dict) -> dict:
    rows = []
    for route in resilience_routes():
        rows.append(
            {
                "focus_survivability_id": stable_row_id("FSV", route.get("route_id"), route.get("dashboard_href")),
                "route_id": route.get("route_id"),
                "dashboard_href": route.get("dashboard_href"),
                "focus_anchor": f"#{route.get('route_type')}-focus",
                "restore_strategy": "static_anchor_return",
                "focus_visible_required": True,
                "survivability_status": "survives_static_route",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_focus_survivability_v1")
    artifact.update({"focus_survivability_registry_id": stable_row_id("FSVREG", [row["focus_survivability_id"] for row in rows]), "focus_survivability_entries": rows, "summary": {"focus_survivability_entry_count": len(rows)}})
    return artifact


def render_focus_survivability_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("focus_survivability_registry") or {}).get("focus_survivability_entries") or []
    return render_resilience_page("Focus Survivability Dashboard", "focus_survivability_dashboard.html", rows, ["route_id", "dashboard_href", "focus_anchor", "restore_strategy", "survivability_status"], "focus_survivability_id", [("Focus routes", len(rows))])
