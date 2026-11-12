"""Validation for imported adjudication events."""

from __future__ import annotations

from adjudication_event_import import EVENT_TYPES, phase38_adjudication_artifact
from stability import deterministic_id


def validate_adjudication_events(event_registry: dict, outputs: dict) -> dict:
    known_conflicts = {row.get("conflict_id") for row in (outputs.get("reconciliation_conflicts") or {}).get("conflicts") or []}
    seen = set()
    valid = []
    invalid = []
    for event in event_registry.get("events") or []:
        errors = []
        event_id = event.get("event_id")
        if not event_id:
            errors.append("missing_event_id")
        if event_id in seen:
            errors.append("duplicate_event_id")
        seen.add(event_id)
        if event.get("event_type") not in EVENT_TYPES:
            errors.append("unsupported_event_type")
        if event.get("conflict_id") not in known_conflicts:
            errors.append("orphaned_conflict_reference")
        if not event.get("append_only") or event.get("history_mutated"):
            errors.append("append_only_violation")
        if event.get("autonomous_resolution_performed") or event.get("operational_state_mutated"):
            errors.append("forbidden_runtime_mutation")
        target = invalid if errors else valid
        target.append({"event_id": event_id, "conflict_id": event.get("conflict_id"), "event_type": event.get("event_type"), "validation_status": "rejected_invalid" if errors else "valid", "errors": errors})
    artifact = phase38_adjudication_artifact("deterministic_adjudication_event_validation_v1")
    artifact.update({"adjudication_event_validation_id": deterministic_id("AEVTVAL", [row.get("event_id") for row in valid], [row.get("event_id") for row in invalid]), "valid_events": valid, "invalid_events": invalid, "summary": {"valid_event_count": len(valid), "invalid_event_count": len(invalid), "append_only_violation_count": sum(1 for row in invalid if "append_only_violation" in row.get("errors", []))}})
    return artifact
