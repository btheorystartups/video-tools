"""Deterministic import of human-authored adjudication events."""

from __future__ import annotations

from reviewer_adjudication import ADJUDICATION_LIMITATION, adjudication_artifact
from review_operational_common import stable_timestamp
from stability import canonical_json, deterministic_id, sha256_text

EVENT_TYPES = {
    "adjudication_decision",
    "escalation_review",
    "governance_review",
    "ambiguity_resolution",
    "deferred_adjudication",
    "consensus_outcome",
    "unresolved_continuation",
}

PHASE38_LIMITATION = (
    "This system provides deterministic operational review, adjudication, and validation workflow support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer "
    "behavior, or make autonomous editorial decisions. Human review is required."
)


def phase38_adjudication_artifact(method: str) -> dict:
    artifact = adjudication_artifact(method)
    artifact["limitations"] = [PHASE38_LIMITATION]
    return artifact


def build_adjudication_event_registry(outputs: dict) -> dict:
    adjudications = (outputs.get("reviewer_adjudication_registry") or {}).get("adjudications") or []
    ambiguities = {row.get("conflict_id"): row for row in (outputs.get("unresolved_ambiguity_registry") or {}).get("ambiguities") or []}
    consensus = {row.get("conflict_id"): row for row in (outputs.get("consensus_workflow_registry") or {}).get("consensus_workflows") or []}
    events = []
    for idx, row in enumerate(adjudications):
        conflict_id = row.get("conflict_id")
        event_type = _event_type(row, ambiguities.get(conflict_id), consensus.get(conflict_id), idx)
        event_id = deterministic_id("AEVT", conflict_id, row.get("adjudication_id"), event_type, idx)
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "source_adjudication_id": row.get("adjudication_id"),
            "conflict_id": conflict_id,
            "human_actor_ref": "local_human_adjudicator_placeholder",
            "event_timestamp": stable_timestamp(event_id),
            "event_source": "deterministic_local_adjudication_event_fixture",
            "decision_text": _decision_text(event_type),
            "rationale_text": "Human-authored adjudication rationale placeholder; pending actual local reviewer import.",
            "provenance_refs": [ref for ref in [row.get("adjudication_id"), conflict_id] if ref],
            "lineage_refs": [ref for ref in [row.get("adjudication_id"), (consensus.get(conflict_id) or {}).get("consensus_workflow_id")] if ref],
            "append_only": True,
            "history_mutated": False,
            "autonomous_resolution_performed": False,
            "operational_state_mutated": False,
            "non_claim_limitation": PHASE38_LIMITATION,
        }
        event["canonical_hash"] = sha256_text(canonical_json(event))
        events.append(event)
    registry = phase38_adjudication_artifact("deterministic_adjudication_event_import_v1")
    registry.update(
        {
            "adjudication_event_registry_id": deterministic_id("AEVTREG", [row["event_id"] for row in events]),
            "allowed_event_types": sorted(EVENT_TYPES),
            "events": events,
            "summary": {
                "event_count": len(events),
                "append_only": True,
                "autonomous_resolution_count": 0,
                "event_type_counts": {event_type: sum(1 for row in events if row["event_type"] == event_type) for event_type in sorted(EVENT_TYPES)},
            },
        }
    )
    return registry


def _event_type(adjudication: dict, ambiguity: dict | None, consensus: dict | None, idx: int) -> str:
    if adjudication.get("escalation_state") in {"governance_arbitration_required", "manual_resolution_required"}:
        return "governance_review"
    if ambiguity and ambiguity.get("ambiguity_types"):
        return "unresolved_continuation"
    if consensus and consensus.get("manual_consensus_required"):
        return "consensus_outcome"
    return ["adjudication_decision", "escalation_review", "deferred_adjudication"][idx % 3]


def _decision_text(event_type: str) -> str:
    if event_type == "unresolved_continuation":
        return "Continue unresolved ambiguity for human review."
    if event_type == "consensus_outcome":
        return "Record pending manual consensus outcome without applying it."
    if event_type == "governance_review":
        return "Escalate to governance review; no automatic adjudication applied."
    return "Record human adjudication event without mutating existing lineage."
