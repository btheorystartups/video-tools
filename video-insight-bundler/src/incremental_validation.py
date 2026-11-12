"""Scoped deterministic validation planning."""

from __future__ import annotations

from generation_dependency_tracker import operational_artifact
from stability import deterministic_id


def build_incremental_validation_plan(validation_index: dict, validation_cache: dict) -> dict:
    cache = {row.get("cache_key"): row for row in validation_cache.get("cache_entries") or []}
    rows = []
    for entry in validation_index.get("validation_entries") or []:
        cached = cache.get(entry.get("cache_key")) or {}
        rows.append({
            "incremental_validation_id": deterministic_id("IVAL", entry.get("artifact"), entry.get("cache_key")),
            "artifact": entry.get("artifact"),
            "validation_scope": entry.get("validation_scope"),
            "changed_artifact_validation": not cached.get("cache_reusable"),
            "dependency_aware_validation": True,
            "validation_reuse_allowed": bool(cached.get("cache_reusable")),
            "validation_manifest_ref": "operations/validation_index.json",
        })
    artifact = operational_artifact("deterministic_incremental_validation_plan_v1")
    artifact.update({"incremental_validation_id": deterministic_id("IVALREG", [row["incremental_validation_id"] for row in rows]), "validation_plan": rows, "summary": {"planned_validation_count": len(rows), "reuse_allowed_count": sum(1 for row in rows if row["validation_reuse_allowed"])}})
    return artifact
