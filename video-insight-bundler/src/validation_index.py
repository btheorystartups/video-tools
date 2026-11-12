"""Incremental validation index generation."""

from __future__ import annotations

from pathlib import Path

from generation_dependency_tracker import ARTIFACT_REFS, operational_artifact
from stability import STATUS_COMPLETE, deterministic_id, sha256_text


def build_validation_index(output_dir: Path, artifact_index: dict, dependency_registry: dict) -> dict:
    deps = {row.get("artifact"): row for row in dependency_registry.get("dependencies") or []}
    rows = []
    for artifact in artifact_index.get("artifacts") or []:
        schema_ref = f"schemas/{artifact.get('artifact')}.schema.json"
        schema_exists = (output_dir / schema_ref).exists()
        rows.append({
            "validation_index_id": deterministic_id("VIDX", artifact.get("artifact"), artifact.get("artifact_hash"), schema_exists),
            "artifact": artifact.get("artifact"),
            "artifact_ref": artifact.get("artifact_ref"),
            "artifact_hash": artifact.get("artifact_hash"),
            "schema_ref": schema_ref,
            "schema_available": schema_exists,
            "dependencies": (deps.get(artifact.get("artifact")) or {}).get("dependencies", []),
            "validation_scope": _scope(artifact.get("artifact")),
            "validation_state": STATUS_COMPLETE if artifact.get("artifact_hash") and schema_exists else "pending",
            "cache_key": sha256_text("|".join(str(v) for v in [artifact.get("artifact"), artifact.get("artifact_hash"), schema_ref])),
        })
    result = operational_artifact("deterministic_validation_index_v1")
    result.update({"validation_index_id": deterministic_id("VIDXREG", [row["validation_index_id"] for row in rows]), "validation_entries": rows, "summary": {"validation_entry_count": len(rows), "complete_validation_entry_count": sum(1 for row in rows if row["validation_state"] == STATUS_COMPLETE), "incremental_validation_supported": True}})
    return result


def _scope(name: str | None) -> str:
    if not name:
        return "unknown"
    if "adjudication" in name or "governance_escalation" in name:
        return "adjudication"
    return "operations"
