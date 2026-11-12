"""Deterministic operational wayfinding panels."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_operational_wayfinding_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 5)
        ids = source_ids(events)
        rows.append(
            {
                "operational_wayfinding_id": stable_row_id("OWF", focus, ids),
                "where_you_are": f"{focus}_continuity_scope",
                "how_you_got_here": ids[:3],
                "related_operational_states": ids[3:],
                "recommended_continuity_path": ids,
                "highest_priority_unresolved_continuity": ids[0] if ids else None,
                "orientation_summary": f"{focus.title()} wayfinding links current scope, prior path, and related states.",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_operational_wayfinding_v1")
    artifact.update({"operational_wayfinding_registry_id": stable_row_id("OWFREG", [row["operational_wayfinding_id"] for row in rows]), "wayfinding_panels": rows, "summary": {"wayfinding_panel_count": len(rows)}})
    return artifact


def render_operational_wayfinding_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_wayfinding_registry") or {}).get("wayfinding_panels") or []
    return render_wayfinding_page("Operational Wayfinding Dashboard", "operational_wayfinding_dashboard.html", rows, ["where_you_are", "highest_priority_unresolved_continuity", "orientation_summary"], "operational_wayfinding_id", [("Wayfinding panels", len(rows))])
