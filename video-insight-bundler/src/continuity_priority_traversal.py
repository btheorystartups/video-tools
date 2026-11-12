"""Deterministic continuity-priority traversal registry."""

from __future__ import annotations

from phase45_interaction_common import all_interaction_events, chain_from_events, phase45_artifact, render_interaction_page, stable_row_id


def build_continuity_priority_registry(outputs: dict) -> dict:
    events = sorted(all_interaction_events(outputs, 64), key=lambda row: (-(row.get("significance_score") or 0), row.get("focus") or "", row.get("source_event_id") or ""))
    rows = chain_from_events(events, "CPTR", "continuity_priority", 24)
    artifact = phase45_artifact("deterministic_continuity_priority_traversal_v1")
    artifact.update({"continuity_priority_registry_id": stable_row_id("CPTRREG", [row["continuity_route_id"] for row in rows]), "priority_traversals": rows, "summary": {"priority_traversal_count": len(rows)}})
    return artifact


def render_continuity_priority_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("continuity_priority_registry") or {}).get("priority_traversals") or []
    return render_interaction_page("Continuity Priority Dashboard", "continuity_priority_dashboard.html", rows, ["route_type", "from_event_id", "to_event_id", "priority_score", "route_status"], "continuity_route_id", [("Priority traversals", len(rows))])
