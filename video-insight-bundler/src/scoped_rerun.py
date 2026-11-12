"""Scoped corpus rerun registry."""

from __future__ import annotations

from generation_dependency_tracker import operational_artifact
from stability import deterministic_id


def build_scoped_rerun_registry(selective_regeneration_registry: dict, dependency_registry: dict) -> dict:
    rows = []
    for scope in selective_regeneration_registry.get("regeneration_scopes") or []:
        rows.append({
            "scoped_rerun_id": deterministic_id("SRERUN", scope.get("scope"), scope.get("affected_artifacts")),
            "scope": scope.get("scope"),
            "rerun_mode": "explicit_local_scope",
            "affected_artifacts": scope.get("affected_artifacts") or [],
            "dependency_aware": True,
            "requires_full_suite": scope.get("scope") == "validation_only",
            "safe_to_skip_unrelated_artifacts": scope.get("scope") != "validation_only",
            "hidden_mutable_state": False,
        })
    artifact = operational_artifact("deterministic_scoped_rerun_registry_v1")
    artifact.update({"scoped_rerun_registry_id": deterministic_id("SRERUNREG", [row["scoped_rerun_id"] for row in rows]), "scoped_reruns": rows, "summary": {"scoped_rerun_count": len(rows), "dependency_aware": True}})
    return artifact
