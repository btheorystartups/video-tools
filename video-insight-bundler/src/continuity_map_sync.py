"""Deterministic continuity map synchronization."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_continuity_map_sync_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 5)
        rows.append(
            {
                "continuity_map_sync_id": stable_row_id("CMS", focus, source_ids(events)),
                "focus": focus,
                "source_event_ids": source_ids(events),
                "graph_highlight_target": f"{focus}_continuity_graph",
                "table_highlight_target": f"{focus}_continuity_table",
                "sync_status": "complete",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_continuity_map_sync_v1")
    artifact.update({"continuity_map_sync_registry_id": stable_row_id("CMSREG", [row["continuity_map_sync_id"] for row in rows]), "sync_entries": rows, "summary": {"sync_entry_count": len(rows)}})
    return artifact


def render_continuity_sync_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_map_sync_registry") or {}).get("sync_entries") or []
    return render_wayfinding_page("Continuity Sync Dashboard", "continuity_sync_dashboard.html", rows, ["focus", "sync_status", "graph_highlight_target", "table_highlight_target"], "continuity_map_sync_id", [("Sync entries", len(rows))])
