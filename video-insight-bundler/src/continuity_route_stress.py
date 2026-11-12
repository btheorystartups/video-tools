"""Deterministic continuity-route stress analysis."""

from __future__ import annotations

from phase46_resilience_common import bounded_score, continuity_edge_count, phase46_artifact, render_resilience_page, resilience_routes, stable_row_id


def build_continuity_route_stress_registry(outputs: dict) -> dict:
    edge_count = continuity_edge_count(outputs)
    rows = []
    for route in resilience_routes():
        burden = edge_count + len(str(route.get("dashboard_href") or ""))
        score = bounded_score(160 - min(burden, 160), 160)
        rows.append(
            {
                "continuity_route_stress_id": stable_row_id("CRS", route.get("route_id"), burden),
                "route_id": route.get("route_id"),
                "dashboard_href": route.get("dashboard_href"),
                "continuity_burden": burden,
                "route_stress_score": score,
                "route_stress_status": "review" if score < 0.35 else "survives",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_continuity_route_stress_v1")
    artifact.update({"continuity_route_stress_registry_id": stable_row_id("CRSREG", [row["continuity_route_stress_id"] for row in rows]), "continuity_route_stress_entries": rows, "summary": {"continuity_route_stress_entry_count": len(rows), "route_stress_review_count": sum(1 for row in rows if row["route_stress_status"] == "review")}})
    return artifact


def render_continuity_route_stress_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_route_stress_registry") or {}).get("continuity_route_stress_entries") or []
    return render_resilience_page("Continuity Route Stress Dashboard", "continuity_route_stress_dashboard.html", rows, ["route_id", "dashboard_href", "continuity_burden", "route_stress_score", "route_stress_status"], "continuity_route_stress_id", [("Route stress entries", len(rows))])
