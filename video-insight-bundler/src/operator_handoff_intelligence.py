"""Deterministic operator handoff intelligence."""

from __future__ import annotations

from phase43_recall_common import events_for_focus, phase43_artifact, render_recall_page, source_ids, stable_row_id


def build_operator_handoff_registry(outputs: dict) -> dict:
    specs = [
        ("unresolved_governance_state", "governance"),
        ("unresolved_escalations", "escalation"),
        ("unresolved_ambiguities", "ambiguity"),
        ("important_historical_shifts", "throughput"),
        ("recent_operational_regressions", "workload"),
        ("high_priority_operational_memory", "survivability"),
    ]
    rows = []
    for packet_type, focus in specs:
        events = events_for_focus(outputs, focus, 5)
        rows.append(
            {
                "operator_handoff_entry_id": stable_row_id("OHI", packet_type, source_ids(events)),
                "handoff_type": packet_type,
                "focus": focus,
                "source_event_ids": source_ids(events),
                "source_event_count": len(events),
                "handoff_summary": f"{packet_type.replace('_', ' ')} sourced from {len(events)} deterministic historical events.",
                "requires_next_operator_review": True,
            }
        )
    artifact = phase43_artifact("deterministic_operator_handoff_intelligence_v1")
    artifact.update({"operator_handoff_registry_id": stable_row_id("OHIREG", [row["operator_handoff_entry_id"] for row in rows]), "handoff_entries": rows, "summary": {"handoff_entry_count": len(rows)}})
    return artifact


def render_operator_handoff_dashboard(outputs: dict) -> dict[str, str]:
    rows = (outputs.get("operator_handoff_registry") or {}).get("handoff_entries") or []
    return render_recall_page("Operator Handoff Dashboard", "operator_handoff_dashboard.html", rows, ["handoff_type", "source_event_count", "handoff_summary"], "operator_handoff_entry_id", [("Handoff entries", len(rows))])
