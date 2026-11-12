"""Deterministic accessibility-first traversal panel registry."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, resilience_routes, stable_row_id


def build_accessibility_traversal_registry(outputs: dict) -> dict:
    rows = []
    for index, route in enumerate(resilience_routes(), start=1):
        rows.append(
            {
                "accessibility_traversal_id": stable_row_id("AXT", route.get("route_id"), index),
                "traversal_order": index,
                "dashboard_href": route.get("dashboard_href"),
                "keyboard_entry_ref": "keyboard_navigation_registry",
                "focus_restore_ref": "focus_survivability_registry",
                "accessibility_first_status": "declared",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_accessibility_first_traversal_v1")
    artifact.update({"accessibility_traversal_registry_id": stable_row_id("AXTREG", [row["accessibility_traversal_id"] for row in rows]), "accessibility_traversal_entries": rows, "summary": {"accessibility_traversal_entry_count": len(rows)}})
    return artifact


def render_accessibility_traversal_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("accessibility_traversal_registry") or {}).get("accessibility_traversal_entries") or []
    return render_resilience_page("Accessibility Traversal Dashboard", "accessibility_traversal_dashboard.html", rows, ["traversal_order", "dashboard_href", "keyboard_entry_ref", "focus_restore_ref", "accessibility_first_status"], "accessibility_traversal_id", [("Traversal entries", len(rows))])
