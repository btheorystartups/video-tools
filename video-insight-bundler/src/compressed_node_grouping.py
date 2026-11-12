"""Deterministic compressed node grouping."""

from __future__ import annotations

from phase44_wayfinding_common import focus_specs, path_for_focus, phase44_artifact, render_wayfinding_page, source_ids, stable_row_id


def build_compressed_node_grouping_registry(outputs: dict) -> dict:
    rows = []
    for focus, _keywords in focus_specs():
        events = path_for_focus(outputs, focus, 10)
        rows.append(
            {
                "compressed_node_grouping_id": stable_row_id("CNG", focus, source_ids(events)),
                "group_type": f"{focus}_compressed_cluster",
                "focus": focus,
                "node_ids": source_ids(events),
                "node_count": len(events),
                "compression_label": f"{focus.title()} cluster ({len(events)} nodes)",
                "expanded_view_available": True,
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_compressed_node_grouping_v1")
    artifact.update({"compressed_node_grouping_registry_id": stable_row_id("CNGREG", [row["compressed_node_grouping_id"] for row in rows]), "node_groups": rows, "summary": {"node_group_count": len(rows)}})
    return artifact


def render_compressed_node_grouping_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("compressed_node_grouping_registry") or {}).get("node_groups") or []
    return render_wayfinding_page("Compressed Node Grouping Dashboard", "compressed_node_grouping_dashboard.html", rows, ["group_type", "node_count", "compression_label", "expanded_view_available"], "compressed_node_grouping_id", [("Node groups", len(rows))])
