"""Selective regeneration registry."""

from __future__ import annotations

from generation_dependency_tracker import operational_artifact
from stability import deterministic_id


SCOPES = {
    "adjudication_only": ["adjudication_event_registry", "adjudication_event_validation", "adjudication_event_lineage", "adjudication_event_provenance", "adjudication_history", "governance_escalation_events", "adjudication_outcome_registry"],
    "dashboards_only": ["adjudication_event_dashboard.html", "adjudication_history_dashboard.html", "adjudication_outcome_dashboard.html", "governance_escalation_dashboard.html", "operational_scalability_dashboard.html", "validation_index_dashboard.html", "selective_regeneration_dashboard.html", "scoped_rerun_dashboard.html", "artifact_operational_index_dashboard.html"],
    "queue_artifacts_only": ["governance_adjudication_queue", "arbitration_required_queue", "consensus_required_queue"],
    "validation_only": ["validation_index", "validation_cache_registry"],
    "operations_only": ["rebuild_manifest", "generation_dependency_registry", "scoped_rerun_registry", "artifact_operational_index"],
}


def build_selective_regeneration_registry(dependency_registry: dict, artifact_index: dict) -> dict:
    rows = []
    for scope, artifacts in sorted(SCOPES.items()):
        rows.append({
            "selective_regeneration_id": deterministic_id("SREGEN", scope, artifacts),
            "scope": scope,
            "affected_artifacts": artifacts,
            "dependency_manifest_ref": "operations/generation_dependency_registry.json",
            "operational_index_ref": "operations/artifact_operational_index.json",
            "explicit_decision_required": True,
            "hidden_mutable_state": False,
        })
    artifact = operational_artifact("deterministic_selective_regeneration_registry_v1")
    artifact.update({"selective_regeneration_registry_id": deterministic_id("SREGENREG", [row["selective_regeneration_id"] for row in rows]), "regeneration_scopes": rows, "summary": {"regeneration_scope_count": len(rows), "explicit_decision_required": True}})
    return artifact
