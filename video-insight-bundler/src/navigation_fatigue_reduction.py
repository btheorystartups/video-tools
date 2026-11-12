"""Deterministic navigation fatigue reduction summaries."""

from __future__ import annotations

from phase46_resilience_common import phase46_artifact, render_resilience_page, stable_row_id


def build_navigation_fatigue_registry(outputs: dict) -> dict:
    compression = (outputs.get("interaction_compression_registry") or {}).get("interaction_compression_entries") or []
    focus = (outputs.get("focus_survivability_registry") or {}).get("focus_survivability_entries") or []
    shortcuts = (outputs.get("operational_shortcut_registry") or {}).get("operational_shortcuts") or []
    rows = []
    patterns = [
        ("compressed_operational_summary", len(compression), "use_static_compressed_routes"),
        ("continuity_focus_restoration", len(focus), "restore_declared_focus_anchor"),
        ("rapid_return_navigation", len(shortcuts), "use_keyboard_jump_registry"),
        ("repeated_route_compression", len(compression), "prefer_compact_route_sequence"),
        ("interruption_survivability", len(focus) + len(shortcuts), "return_to_last_focus_or_shortcut"),
    ]
    for scope, support_count, strategy in patterns:
        rows.append(
            {
                "navigation_fatigue_id": stable_row_id("NFR", scope, support_count),
                "fatigue_scope": scope,
                "supporting_entry_count": support_count,
                "reduction_strategy": strategy,
                "fatigue_reduction_status": "available" if support_count else "limited",
                "human_review_required": True,
            }
        )
    artifact = phase46_artifact("deterministic_navigation_fatigue_reduction_v1")
    artifact.update({"navigation_fatigue_registry_id": stable_row_id("NFRREG", [row["navigation_fatigue_id"] for row in rows]), "navigation_fatigue_entries": rows, "summary": {"navigation_fatigue_entry_count": len(rows)}})
    return artifact


def render_navigation_fatigue_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("navigation_fatigue_registry") or {}).get("navigation_fatigue_entries") or []
    return render_resilience_page("Navigation Fatigue Dashboard", "navigation_fatigue_dashboard.html", rows, ["fatigue_scope", "supporting_entry_count", "reduction_strategy", "fatigue_reduction_status"], "navigation_fatigue_id", [("Fatigue entries", len(rows))])
