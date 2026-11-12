"""Deterministic keyboard navigation registry for dense operational dashboards."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, resilience_routes, stable_row_id


def build_keyboard_navigation_registry(outputs: dict) -> dict:
    actions = [
        ("dashboard_jump", "Alt+1", "jump_to_dashboard_index"),
        ("continuity_next", "Alt+Right", "move_to_next_continuity_route"),
        ("continuity_previous", "Alt+Left", "move_to_previous_continuity_route"),
        ("breadcrumb_back", "Alt+Up", "return_to_parent_breadcrumb"),
        ("review_route", "Alt+R", "open_linked_review_pathway"),
        ("pagination_next", "PageDown", "advance_static_page"),
        ("pagination_previous", "PageUp", "return_static_page"),
        ("focus_restore", "Alt+F", "restore_last_declared_focus_anchor"),
    ]
    rows = []
    routes = resilience_routes()
    for index, (scope, key_binding, action) in enumerate(actions):
        route = routes[index % len(routes)] if routes else {}
        rows.append(
            {
                "keyboard_navigation_id": stable_row_id("KBD", scope, key_binding, action),
                "navigation_scope": scope,
                "key_binding": key_binding,
                "deterministic_action": action,
                "target_dashboard_href": route.get("dashboard_href"),
                "focus_restore_supported": scope == "focus_restore",
                "navigation_status": "available",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_keyboard_navigation_system_v1")
    artifact.update({"keyboard_navigation_registry_id": stable_row_id("KBDREG", [row["keyboard_navigation_id"] for row in rows]), "keyboard_navigation_entries": rows, "summary": {"keyboard_navigation_entry_count": len(rows)}})
    return artifact


def render_keyboard_navigation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("keyboard_navigation_registry") or {}).get("keyboard_navigation_entries") or []
    return render_resilience_page("Keyboard Navigation Dashboard", "keyboard_navigation_dashboard.html", rows, ["navigation_scope", "key_binding", "deterministic_action", "target_dashboard_href", "navigation_status"], "keyboard_navigation_id", [("Keyboard entries", len(rows))])
