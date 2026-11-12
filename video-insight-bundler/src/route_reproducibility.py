"""Deterministic route reproducibility proofing."""

from __future__ import annotations

from phase47_replay_common import phase47_artifact, render_replay_page, replay_routes, stable_row_id


def build_route_reproducibility_registry(outputs: dict) -> dict:
    rows = []
    for route in replay_routes():
        href = route.get("dashboard_href") or ""
        rows.append(
            {
                "route_reproducibility_id": stable_row_id("RRP", route.get("route_id"), href),
                "route_id": route.get("route_id"),
                "route_type": route.get("route_type"),
                "dashboard_href": href,
                "relative_route": href.startswith("../") or not href.startswith(("http://", "https://")),
                "route_reproducibility_status": "reproducible" if href else "review",
                "human_review_required": True,
            }
        )
    artifact = phase47_artifact("deterministic_route_reproducibility_v1")
    artifact.update({"route_reproducibility_registry_id": stable_row_id("RRPREG", [row["route_reproducibility_id"] for row in rows]), "route_reproducibility_entries": rows, "summary": {"route_reproducibility_entry_count": len(rows)}})
    return artifact


def render_route_reproducibility_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("route_reproducibility_registry") or {}).get("route_reproducibility_entries") or []
    return render_replay_page("Route Reproducibility Dashboard", "route_reproducibility_dashboard.html", rows, ["route_type", "dashboard_href", "relative_route", "route_reproducibility_status"], "route_reproducibility_id", [("Route proofs", len(rows))])
