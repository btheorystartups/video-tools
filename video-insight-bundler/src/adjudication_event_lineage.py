"""Lineage for human adjudication events."""

from __future__ import annotations

from adjudication_event_import import phase38_adjudication_artifact
from review_operational_common import stable_timestamp
from stability import deterministic_id


def build_adjudication_event_lineage(event_registry: dict, event_validation: dict, outputs: dict) -> dict:
    valid_ids = {row.get("event_id") for row in event_validation.get("valid_events") or []}
    previous = {row.get("conflict_id"): row for row in (outputs.get("adjudication_lineage") or {}).get("lineage_entries") or []}
    rows = []
    for event in event_registry.get("events") or []:
        prior = previous.get(event.get("conflict_id")) or {}
        lineage_id = deterministic_id("AEVTLIN", event.get("event_id"), prior.get("lineage_id"))
        rows.append({
            "event_lineage_id": lineage_id,
            "event_id": event.get("event_id"),
            "conflict_id": event.get("conflict_id"),
            "timestamp": stable_timestamp(lineage_id),
            "validation_state": "valid" if event.get("event_id") in valid_ids else "invalid",
            "lineage_steps": [
                {"step": "phase37_adjudication_lineage", "refs": [prior.get("lineage_id")] if prior.get("lineage_id") else []},
                {"step": "human_adjudication_event_import", "refs": [event.get("event_id")]},
                {"step": "event_validation", "refs": [event_validation.get("adjudication_event_validation_id")]},
                {"step": "append_only_history", "refs": ["adjudication_history.json"]},
            ],
            "append_only": True,
            "lineage_mutated": False,
        })
    artifact = phase38_adjudication_artifact("deterministic_adjudication_event_lineage_v1")
    artifact.update({"adjudication_event_lineage_id": deterministic_id("AEVTLINREG", [row["event_lineage_id"] for row in rows]), "lineage_entries": rows, "summary": {"lineage_entry_count": len(rows), "append_only": True}})
    return artifact
