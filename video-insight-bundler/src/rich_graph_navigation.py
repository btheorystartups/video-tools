"""Deterministic rich graph navigation affordances."""

from __future__ import annotations

from phase45_interaction_common import graph_edge_rows, graph_node_ids, operational_score, phase45_artifact, render_interaction_page, stable_row_id


def build_graph_navigation_registry(outputs: dict) -> dict:
    nodes = sorted(graph_node_ids(outputs))
    edge_count = len(graph_edge_rows(outputs))
    rows = []
    for index, node_id in enumerate(nodes[:72]):
        focus = "continuity" if index % 3 == 0 else "operational"
        rows.append(
            {
                "graph_navigation_id": stable_row_id("GNAV", node_id, index),
                "node_id": node_id,
                "group_label": f"{focus}_cluster_{index // 8 + 1}",
                "continuity_emphasis": "high" if focus == "continuity" else "normal",
                "path_highlight_available": True,
                "node_priority_visibility": round(1.0 - min(index, 50) / 100, 3),
                "compact_cluster_available": True,
                "human_review_required": True,
            }
        )
    artifact = phase45_artifact("deterministic_rich_graph_navigation_v1")
    artifact.update({"graph_navigation_registry_id": stable_row_id("GNAVREG", [row["graph_navigation_id"] for row in rows]), "graph_navigation_affordances": rows, "summary": {"graph_navigation_count": len(rows), "graph_node_count": len(nodes), "graph_edge_count": edge_count}})
    return artifact


def render_graph_navigation_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("graph_navigation_registry") or {}).get("graph_navigation_affordances") or []
    return render_interaction_page("Graph Navigation Dashboard", "graph_navigation_dashboard.html", rows, ["node_id", "group_label", "continuity_emphasis", "path_highlight_available", "node_priority_visibility"], "graph_navigation_id", [("Graph affordances", len(rows))])
