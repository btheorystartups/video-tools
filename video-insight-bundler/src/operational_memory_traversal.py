"""Deterministic operational memory traversal."""

from __future__ import annotations

from phase43_recall_common import phase43_artifact, recall_source_events, render_recall_page, stable_row_id


def build_operational_memory_traversal_registry(outputs: dict) -> dict:
    events = recall_source_events(outputs)[:20]
    rows = []
    for index, event in enumerate(events):
        previous_event = events[index - 1] if index else None
        next_event = events[index + 1] if index + 1 < len(events) else None
        rows.append(
            {
                "operational_memory_traversal_id": stable_row_id("OMT", event.get("source_event_id"), previous_event.get("source_event_id") if previous_event else "start", next_event.get("source_event_id") if next_event else "end"),
                "event_id": event.get("source_event_id"),
                "previous_event_id": previous_event.get("source_event_id") if previous_event else None,
                "next_event_id": next_event.get("source_event_id") if next_event else None,
                "focus": event.get("focus"),
                "summary": event.get("summary"),
                "human_review_required": True,
            }
        )
    artifact = phase43_artifact("deterministic_operational_memory_traversal_v1")
    artifact.update({"operational_memory_traversal_registry_id": stable_row_id("OMTREG", [row["operational_memory_traversal_id"] for row in rows]), "traversal_links": rows, "summary": {"traversal_link_count": len(rows)}})
    return artifact


def render_operational_memory_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operational_memory_traversal_registry") or {}).get("traversal_links") or []
    return render_recall_page("Operational Memory Dashboard", "operational_memory_dashboard.html", rows, ["focus", "event_id", "previous_event_id", "next_event_id", "summary"], "operational_memory_traversal_id", [("Traversal links", len(rows))])
