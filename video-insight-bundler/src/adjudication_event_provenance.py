"""Provenance records for imported adjudication events."""

from __future__ import annotations

from adjudication_event_import import PHASE38_LIMITATION, phase38_adjudication_artifact
from stability import deterministic_id


def build_adjudication_event_provenance(event_registry: dict, event_validation: dict) -> dict:
    valid_ids = {row.get("event_id") for row in event_validation.get("valid_events") or []}
    rows = []
    for event in event_registry.get("events") or []:
        rows.append({
            "provenance_id": deterministic_id("AEVTPROV", event.get("event_id"), event.get("canonical_hash")),
            "event_id": event.get("event_id"),
            "source": event.get("event_source"),
            "human_actor_ref": event.get("human_actor_ref"),
            "canonical_hash": event.get("canonical_hash"),
            "source_adjudication_id": event.get("source_adjudication_id"),
            "validation_state": "valid" if event.get("event_id") in valid_ids else "invalid",
            "provenance_preserved": True,
            "non_claim_limitation": PHASE38_LIMITATION,
        })
    artifact = phase38_adjudication_artifact("deterministic_adjudication_event_provenance_v1")
    artifact.update({"adjudication_event_provenance_id": deterministic_id("AEVTPROVREG", [row["provenance_id"] for row in rows]), "provenance_entries": rows, "summary": {"provenance_entry_count": len(rows), "provenance_preserved": True}})
    return artifact
