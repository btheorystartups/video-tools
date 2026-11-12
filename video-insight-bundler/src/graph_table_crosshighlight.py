"""Deterministic graph/table cross-highlighting registry."""

from __future__ import annotations

from phase44_wayfinding_common import all_wayfinding_events, graph_edges, phase44_artifact, render_wayfinding_page, stable_row_id


def build_graph_crosshighlight_registry(outputs: dict) -> dict:
    events = {row.get("source_event_id"): row for row in all_wayfinding_events(outputs)}
    rows = []
    for edge in graph_edges(outputs)[:24]:
        from_id = edge.get("from_node_id")
        to_id = edge.get("to_node_id")
        rows.append(
            {
                "graph_crosshighlight_id": stable_row_id("GTH", from_id, to_id, edge.get("relationship_type")),
                "graph_node_ids": [value for value in [from_id, to_id] if value],
                "table_row_ids": [value for value in [from_id, to_id] if value in events],
                "highlight_mode": "graph_table_bidirectional",
                "continuity_path_synchronized": bool(from_id and to_id),
                "related_event_synchronized": True,
                "milestone_synchronized": edge.get("relationship_type") == "narrative_sequence",
                "human_review_required": True,
            }
        )
    artifact = phase44_artifact("deterministic_graph_table_crosshighlight_v1")
    artifact.update({"graph_crosshighlight_registry_id": stable_row_id("GTHREG", [row["graph_crosshighlight_id"] for row in rows]), "crosshighlights": rows, "summary": {"crosshighlight_count": len(rows)}})
    return artifact


def render_graph_crosshighlight_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("graph_crosshighlight_registry") or {}).get("crosshighlights") or []
    return render_wayfinding_page("Graph Crosshighlight Dashboard", "graph_crosshighlight_dashboard.html", rows, ["highlight_mode", "graph_node_ids", "table_row_ids", "continuity_path_synchronized"], "graph_crosshighlight_id", [("Cross-highlights", len(rows))])
