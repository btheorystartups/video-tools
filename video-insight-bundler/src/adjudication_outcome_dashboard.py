"""Adjudication outcome registry and static dashboard rendering."""

from __future__ import annotations

from dashboard_layout import e
from adjudication_event_import import PHASE38_LIMITATION, phase38_adjudication_artifact
from reviewer_adjudication import ADJUDICATION_LIMITATION
from review_operational_common import card_grid, compact_metrics, simple_review_page
from stability import deterministic_id


def build_adjudication_outcome_registry(event_registry: dict, history: dict, escalation_events: dict) -> dict:
    escalation_ids = {row.get("event_id") for row in escalation_events.get("escalation_events") or []}
    rows = []
    for event in event_registry.get("events") or []:
        rows.append({
            "outcome_id": deterministic_id("ADJOUT", event.get("event_id")),
            "event_id": event.get("event_id"),
            "conflict_id": event.get("conflict_id"),
            "outcome_state": "requires_human_governance_review" if event.get("event_id") in escalation_ids else "recorded_pending_manual_review",
            "history_ref": history.get("adjudication_history_id"),
            "escalation_imported": event.get("event_id") in escalation_ids,
            "autonomous_resolution_performed": False,
        })
    artifact = phase38_adjudication_artifact("deterministic_adjudication_outcome_registry_v1")
    artifact.update({"adjudication_outcome_registry_id": deterministic_id("ADJOUTREG", [row["outcome_id"] for row in rows]), "outcomes": rows, "summary": {"outcome_count": len(rows), "escalated_outcome_count": sum(1 for row in rows if row["escalation_imported"])}})
    return artifact


def render_adjudication_event_dashboards(outputs: dict) -> dict[str, str]:
    links = [
        ("Dashboard", "../dashboard.html"),
        ("Events", "adjudication_event_dashboard.html"),
        ("History", "adjudication_history_dashboard.html"),
        ("Outcomes", "adjudication_outcome_dashboard.html"),
        ("Escalations", "governance_escalation_dashboard.html"),
        ("Conflict Resolution", "conflict_resolution_dashboard.html"),
    ]
    limitation = f"<section class='panel'><p>{e(PHASE38_LIMITATION)}</p><p>{e(ADJUDICATION_LIMITATION)}</p></section>"
    events = (outputs.get("adjudication_event_registry") or {}).get("events") or []
    history = (outputs.get("adjudication_history") or {}).get("history_entries") or []
    outcomes = (outputs.get("adjudication_outcome_registry") or {}).get("outcomes") or []
    escalations = (outputs.get("governance_escalation_events") or {}).get("escalation_events") or []
    return {
        "adjudication_event_dashboard.html": simple_review_page("Adjudication Event Dashboard", "Adjudication Events", "adjudication_event_dashboard.html", limitation + compact_metrics([("Events", len(events)), ("Escalations", len(escalations))]) + card_grid(events, ["event_type", "conflict_id", "decision_text", "append_only"], "event_id"), links),
        "adjudication_history_dashboard.html": simple_review_page("Adjudication History Dashboard", "Adjudication History", "adjudication_history_dashboard.html", limitation + card_grid(history, ["sequence_index", "event_type", "conflict_id", "append_only"], "history_entry_id"), links),
        "adjudication_outcome_dashboard.html": simple_review_page("Adjudication Outcome Dashboard", "Adjudication Outcomes", "adjudication_outcome_dashboard.html", limitation + card_grid(outcomes, ["conflict_id", "outcome_state", "escalation_imported"], "outcome_id"), links),
        "governance_escalation_dashboard.html": simple_review_page("Governance Escalation Dashboard", "Governance Escalations", "governance_escalation_dashboard.html", limitation + card_grid(escalations, ["conflict_id", "governance_severity", "escalation_reason", "requires_human_governance_review"], "escalation_event_id"), links),
    }
