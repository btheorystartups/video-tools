"""Deterministic orphaned state detection."""

from __future__ import annotations

from phase44_wayfinding_common import all_wayfinding_events, graph_edges, phase44_artifact, render_wayfinding_page, stable_row_id


def build_orphaned_state_registry(outputs: dict) -> dict:
    linked = set()
    for edge in graph_edges(outputs):
        linked.add(edge.get("from_node_id"))
        linked.add(edge.get("to_node_id"))
    rows = []
    for event in all_wayfinding_events(outputs, 48):
        event_id = event.get("source_event_id")
        if event_id and event_id not in linked:
            rows.append(
                {
                    "orphaned_state_id": stable_row_id("ORP", event_id),
                    "event_id": event_id,
                    "focus": event.get("focus"),
                    "orphan_type": f"isolated_{event.get('focus')}_state",
                    "detection_reason": "event lacks graph continuity edge in current deterministic recall graph",
                    "human_review_required": True,
                }
            )
    artifact = phase44_artifact("deterministic_orphaned_state_detection_v1")
    artifact.update({"orphaned_state_registry_id": stable_row_id("ORPREG", [row["orphaned_state_id"] for row in rows]), "orphaned_states": rows, "summary": {"orphaned_state_count": len(rows)}})
    return artifact


def render_orphaned_state_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("orphaned_state_registry") or {}).get("orphaned_states") or []
    return render_wayfinding_page("Orphaned State Dashboard", "orphaned_state_dashboard.html", rows, ["focus", "orphan_type", "detection_reason"], "orphaned_state_id", [("Orphaned states", len(rows))])
