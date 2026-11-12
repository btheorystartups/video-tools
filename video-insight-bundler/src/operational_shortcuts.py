"""Deterministic operational shortcut registry."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, stable_row_id


def build_operational_shortcut_registry(outputs: dict) -> dict:
    keyboard_rows = (outputs.get("keyboard_navigation_registry") or {}).get("keyboard_navigation_entries") or []
    rows = []
    for row in keyboard_rows:
        rows.append(
            {
                "operational_shortcut_id": stable_row_id("OSK", row.get("keyboard_navigation_id")),
                "shortcut_scope": row.get("navigation_scope"),
                "key_binding": row.get("key_binding"),
                "shortcut_purpose": row.get("deterministic_action"),
                "declared_in_keyboard_registry": True,
                "shortcut_status": "registered",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_operational_shortcuts_v1")
    artifact.update({"operational_shortcut_registry_id": stable_row_id("OSKREG", [row["operational_shortcut_id"] for row in rows]), "operational_shortcuts": rows, "summary": {"operational_shortcut_count": len(rows)}})
    return artifact


def render_operational_shortcuts_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_shortcut_registry") or {}).get("operational_shortcuts") or []
    return render_resilience_page("Operational Shortcuts Dashboard", "operational_shortcuts_dashboard.html", rows, ["shortcut_scope", "key_binding", "shortcut_purpose", "shortcut_status"], "operational_shortcut_id", [("Shortcuts", len(rows))])
