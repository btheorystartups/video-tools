"""Operational rebuild manifest."""

from __future__ import annotations

from generation_dependency_tracker import operational_artifact
from stability import deterministic_id


def build_rebuild_manifest(artifact_index: dict, dependency_registry: dict, validation_index: dict) -> dict:
    validation = {row.get("artifact"): row for row in validation_index.get("validation_entries") or []}
    rows = []
    for artifact in artifact_index.get("artifacts") or []:
        rows.append({
            "rebuild_entry_id": deterministic_id("RBLD", artifact.get("artifact"), artifact.get("artifact_hash")),
            "artifact": artifact.get("artifact"),
            "artifact_ref": artifact.get("artifact_ref"),
            "artifact_hash": artifact.get("artifact_hash"),
            "dependencies": artifact.get("dependencies") or [],
            "rebuild_relevance": artifact.get("rebuild_relevance"),
            "validation_state": (validation.get(artifact.get("artifact")) or {}).get("validation_state", "pending"),
            "selective_regeneration_allowed": True,
        })
    manifest = operational_artifact("deterministic_rebuild_manifest_v1")
    manifest.update({"rebuild_manifest_id": deterministic_id("RBLDREG", [row["rebuild_entry_id"] for row in rows]), "rebuild_entries": rows, "summary": {"rebuild_entry_count": len(rows), "selective_regeneration_allowed": True, "dependency_aware_rebuilds": True}})
    return manifest
