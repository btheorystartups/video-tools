"""Governance escalation event import records."""

from __future__ import annotations

from adjudication_event_import import phase38_adjudication_artifact
from review_operational_common import stable_timestamp
from stability import deterministic_id


def build_governance_escalation_events(event_registry: dict, outputs: dict) -> dict:
    conflicts = {row.get("conflict_id"): row for row in (outputs.get("governance_conflict_analysis") or {}).get("governance_conflicts") or []}
    rows = []
    for event in event_registry.get("events") or []:
        conflict = conflicts.get(event.get("conflict_id")) or {}
        if event.get("event_type") in {"governance_review", "escalation_review", "unresolved_continuation"} or conflict.get("requires_arbitration"):
            escalation_id = deterministic_id("GESC", event.get("event_id"), conflict.get("governance_conflict_id"))
            rows.append({
                "escalation_event_id": escalation_id,
                "event_id": event.get("event_id"),
                "conflict_id": event.get("conflict_id"),
                "timestamp": stable_timestamp(escalation_id),
                "governance_severity": conflict.get("governance_severity", "review"),
                "escalation_reason": conflict.get("governance_impact_summary", "manual governance escalation import"),
                "requires_human_governance_review": True,
                "append_only": True,
                "autonomous_resolution_performed": False,
            })
    artifact = phase38_adjudication_artifact("deterministic_governance_escalation_import_v1")
    artifact.update({"governance_escalation_events_id": deterministic_id("GESCREG", [row["escalation_event_id"] for row in rows]), "escalation_events": rows, "summary": {"escalation_event_count": len(rows), "requires_human_governance_review": bool(rows)}})
    return artifact
