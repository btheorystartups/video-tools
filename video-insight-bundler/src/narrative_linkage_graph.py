"""Deterministic narrative linkage graph."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, recall_source_events, render_recall_page, stable_row_id


def build_narrative_linkage_graph_registry(outputs: dict) -> dict:
    events = recall_source_events(outputs)[:24]
    nodes = [
        {
            "node_id": event.get("source_event_id"),
            "node_type": event.get("focus"),
            "label": event.get("source_type"),
            "summary": event.get("summary"),
            "significance_score": event.get("significance_score"),
        }
        for event in events
    ]
    edges = []
    for index, event in enumerate(events[:-1]):
        next_event = events[index + 1]
        if event.get("focus") == next_event.get("focus") or index % 3 == 0:
            edges.append(
                {
                    "edge_id": stable_row_id("NLGEDGE", event.get("source_event_id"), next_event.get("source_event_id")),
                    "from_node_id": event.get("source_event_id"),
                    "to_node_id": next_event.get("source_event_id"),
                    "relationship_type": f"{event.get('focus')}_continuity" if event.get("focus") == next_event.get("focus") else "narrative_sequence",
                    "human_review_required": True,
                }
            )
    artifact = phase43_artifact("deterministic_narrative_linkage_graph_v1")
    artifact.update({"narrative_linkage_graph_registry_id": stable_row_id("NLGREG", [node["node_id"] for node in nodes], [edge["edge_id"] for edge in edges]), "nodes": nodes, "edges": edges, "summary": {"node_count": len(nodes), "edge_count": len(edges)}})
    return artifact


def render_narrative_linkage_dashboard(outputs: dict) -> dict[str, str]:
    graph = outputs.get("narrative_linkage_graph_registry") or {}
    rows = graph.get("edges") or []
    return render_recall_page("Narrative Linkage Dashboard", "narrative_linkage_dashboard.html", rows, ["relationship_type", "from_node_id", "to_node_id"], "edge_id", [("Nodes", len(graph.get("nodes") or [])), ("Edges", len(rows))])
