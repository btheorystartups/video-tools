"""Deterministic compact dashboard navigation layers."""

from __future__ import annotations

from phase45_interaction_common import phase45_artifact, render_interaction_page, route_rows, stable_row_id


def build_compact_dashboard_navigation_registry(outputs: dict) -> dict:
    routes = route_rows()
    rows = []
    for index in range(0, len(routes), 4):
        chunk = routes[index : index + 4]
        rows.append(
            {
                "compact_navigation_layer_id": stable_row_id("CDNAV", index, [row["route_id"] for row in chunk]),
                "layer_number": index // 4 + 1,
                "dashboard_count": len(chunk),
                "dashboard_hrefs": [row["dashboard_href"] for row in chunk],
                "layer_status": "complete",
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_compact_dashboard_navigation_v1")
    artifact.update({"compact_navigation_registry_id": stable_row_id("CDNAVREG", [row["compact_navigation_layer_id"] for row in rows]), "compact_navigation_layers": rows, "summary": {"compact_navigation_layer_count": len(rows)}})
    return artifact


def render_compact_navigation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("compact_dashboard_navigation_registry") or {}).get("compact_navigation_layers") or []
    return render_interaction_page("Compact Navigation Dashboard", "compact_navigation_dashboard.html", rows, ["layer_number", "dashboard_count", "dashboard_hrefs", "layer_status"], "compact_navigation_layer_id", [("Navigation layers", len(rows))])
