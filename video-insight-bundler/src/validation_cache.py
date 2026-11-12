"""Artifact-hash-aware validation cache registry."""

from __future__ import annotations

from generation_dependency_tracker import operational_artifact
from stability import deterministic_id


def build_validation_cache_registry(validation_index: dict) -> dict:
    rows = []
    for entry in validation_index.get("validation_entries") or []:
        rows.append({
            "cache_entry_id": deterministic_id("VCACHE", entry.get("cache_key")),
            "artifact": entry.get("artifact"),
            "cache_key": entry.get("cache_key"),
            "artifact_hash": entry.get("artifact_hash"),
            "schema_ref": entry.get("schema_ref"),
            "validation_state": entry.get("validation_state"),
            "cache_reusable": bool(entry.get("artifact_hash") and entry.get("schema_available")),
            "invalidation_rule": "invalidate_when_artifact_hash_or_schema_ref_changes",
            "hidden_mutable_state": False,
        })
    artifact = operational_artifact("deterministic_validation_cache_registry_v1")
    artifact.update({"validation_cache_registry_id": deterministic_id("VCACHEREG", [row["cache_entry_id"] for row in rows]), "cache_entries": rows, "summary": {"cache_entry_count": len(rows), "reusable_cache_entry_count": sum(1 for row in rows if row["cache_reusable"]), "hidden_mutable_state": False}})
    return artifact
