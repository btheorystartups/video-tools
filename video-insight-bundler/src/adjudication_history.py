"""Append-only adjudication history assembled from imported events."""

from __future__ import annotations

from adjudication_event_import import phase38_adjudication_artifact
from review_operational_common import stable_timestamp
from stability import deterministic_id


def build_adjudication_history(event_registry: dict, event_lineage: dict, event_provenance: dict) -> dict:
    lineage = {row.get("event_id"): row for row in event_lineage.get("lineage_entries") or []}
    provenance = {row.get("event_id"): row for row in event_provenance.get("provenance_entries") or []}
    rows = []
    for idx, event in enumerate(event_registry.get("events") or []):
        history_id = deterministic_id("ADJHIST", event.get("event_id"), idx)
        rows.append({
            "history_entry_id": history_id,
            "sequence_index": idx,
            "timestamp": stable_timestamp(history_id),
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "conflict_id": event.get("conflict_id"),
            "decision_text": event.get("decision_text"),
            "lineage_id": (lineage.get(event.get("event_id")) or {}).get("event_lineage_id"),
            "provenance_id": (provenance.get(event.get("event_id")) or {}).get("provenance_id"),
            "append_only": True,
            "history_mutated": False,
            "autonomous_resolution_performed": False,
        })
    artifact = phase38_adjudication_artifact("deterministic_adjudication_history_v1")
    artifact.update({"adjudication_history_id": deterministic_id("ADJHISTREG", [row["history_entry_id"] for row in rows]), "history_entries": rows, "summary": {"history_entry_count": len(rows), "append_only": True, "history_mutation_count": 0}})
    return artifact
