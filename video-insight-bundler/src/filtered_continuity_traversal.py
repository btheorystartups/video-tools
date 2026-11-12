"""Deterministic filtered continuity traversal."""

from __future__ import annotations

from phase44_wayfinding_common import continuity_pairs, focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, stable_row_id


def build_filtered_continuity_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        rows.extend(continuity_pairs(path_for_focus(outputs, focus, 6), "FCT", f"{focus}_filtered_traversal"))
    artifact = phase44_artifact("deterministic_filtered_continuity_traversal_v1")
    artifact.update({"filtered_continuity_registry_id": stable_row_id("FCTREG", [row["continuity_path_id"] for row in rows]), "filtered_paths": rows, "summary": {"filtered_path_count": len(rows)}})
    return artifact


def render_filtered_continuity_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("filtered_continuity_registry") or {}).get("filtered_paths") or []
    return render_wayfinding_page("Filtered Continuity Dashboard", "filtered_continuity_dashboard.html", rows, ["relation_type", "from_event_id", "to_event_id", "path_status"], "continuity_path_id", [("Filtered paths", len(rows))])
