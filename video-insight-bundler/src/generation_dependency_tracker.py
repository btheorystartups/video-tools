"""Deterministic generation dependency registry."""

from __future__ import annotations

from pathlib import Path

from adjudication_event_import import PHASE38_LIMITATION
from intelligence_common import base_artifact
from stability import STATUS_COMPLETE, deterministic_id


DEPENDENCIES = {
    "adjudication_event_registry": ["reviewer_adjudication_registry", "consensus_workflow_registry", "unresolved_ambiguity_registry"],
    "adjudication_event_validation": ["adjudication_event_registry", "reconciliation_conflicts"],
    "adjudication_event_lineage": ["adjudication_event_registry", "adjudication_event_validation", "adjudication_lineage"],
    "adjudication_event_provenance": ["adjudication_event_registry", "adjudication_event_validation"],
    "adjudication_history": ["adjudication_event_registry", "adjudication_event_lineage", "adjudication_event_provenance"],
    "governance_escalation_events": ["adjudication_event_registry", "governance_conflict_analysis"],
    "adjudication_outcome_registry": ["adjudication_event_registry", "adjudication_history", "governance_escalation_events"],
    "rebuild_manifest": ["artifact_operational_index", "generation_dependency_registry"],
    "validation_index": ["artifact_operational_index", "generation_dependency_registry"],
    "validation_cache_registry": ["validation_index"],
    "selective_regeneration_registry": ["generation_dependency_registry", "artifact_operational_index"],
    "scoped_rerun_registry": ["selective_regeneration_registry", "generation_dependency_registry"],
    "artifact_operational_index": ["adjudication_event_registry", "adjudication_history"],
    "import_preview_registry": ["review_import_registry", "review_import_validation"],
    "validation_preview_registry": ["import_preview_registry", "review_import_validation"],
    "reconciliation_preview_registry": ["import_preview_registry", "reconciliation_conflicts"],
    "operator_import_review_registry": ["import_preview_registry", "validation_preview_registry", "reconciliation_preview_registry"],
    "performance_profile_registry": ["validation_index", "dashboard_render_registry", "adjudication_event_registry"],
    "validation_timing_registry": ["validation_index"],
    "rebuild_cost_registry": ["artifact_operational_index", "generation_dependency_registry"],
    "artifact_density_registry": ["artifact_operational_index"],
    "dashboard_render_registry": ["artifact_operational_index"],
    "queue_scaling_registry": ["review_queue_registry", "adjudication_queue_registry", "validation_index"],
    "throughput_analysis_registry": ["review_queue_registry", "adjudication_queue_registry", "review_packet_export_registry"],
    "workload_heatmap_registry": ["review_queue_registry", "adjudication_event_registry", "validation_index"],
    "scalability_warning_registry": ["queue_scaling_registry", "validation_timing_registry", "rebuild_cost_registry", "artifact_density_registry"],
    "session_ergonomics_registry": ["review_queue_registry", "dashboard_render_registry", "unresolved_ambiguity_registry"],
    "progressive_disclosure_registry": ["review_queue_registry", "inline_evidence_preview_index", "recommendation_ranking"],
    "queue_chunking_registry": ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue"],
    "session_focus_restore_registry": ["review_session_registry", "review_checkpoints", "unresolved_ambiguity_registry"],
    "review_bookmark_registry": ["review_queue_registry", "adjudication_queue_registry", "queue_chunking_registry"],
    "interruption_recovery_registry": ["session_focus_restore_registry", "high_priority_review_queue", "adjudication_queue_registry"],
    "operator_attention_heatmap_registry": ["unresolved_ambiguity_registry", "governance_conflict_analysis", "interruption_recovery_registry"],
    "dense_dashboard_pagination_registry": ["queue_chunking_registry", "operator_attention_heatmap_registry", "empirical_benchmark_history"],
    "fatigue_reduction_registry": ["queue_chunking_registry", "progressive_disclosure_registry", "inline_evidence_preview_index"],
    "empirical_benchmark_history": ["performance_profile_registry", "validation_timing_registry", "dashboard_render_registry", "rebuild_cost_registry"],
    "repeated_benchmark_snapshots": ["empirical_benchmark_history"],
    "local_benchmark_baselines": ["empirical_benchmark_history"],
    "performance_drift_registry": ["empirical_benchmark_history", "local_benchmark_baselines"],
    "benchmark_comparison_history": ["empirical_benchmark_history", "performance_drift_registry"],
    "compact_navigation_registry": ["queue_chunking_registry", "session_focus_restore_registry", "performance_drift_registry", "operator_attention_heatmap_registry"],
}


ARTIFACT_REFS = {
    "adjudication_event_registry": "adjudication_events/adjudication_event_registry.json",
    "adjudication_event_validation": "adjudication_events/adjudication_event_validation.json",
    "adjudication_event_lineage": "adjudication_events/adjudication_event_lineage.json",
    "adjudication_event_provenance": "adjudication_events/adjudication_event_provenance.json",
    "adjudication_history": "adjudication_events/adjudication_history.json",
    "governance_escalation_events": "adjudication_events/governance_escalation_events.json",
    "adjudication_outcome_registry": "adjudication_events/adjudication_outcome_registry.json",
    "rebuild_manifest": "operations/rebuild_manifest.json",
    "validation_index": "operations/validation_index.json",
    "validation_cache_registry": "operations/validation_cache_registry.json",
    "selective_regeneration_registry": "operations/selective_regeneration_registry.json",
    "generation_dependency_registry": "operations/generation_dependency_registry.json",
    "scoped_rerun_registry": "operations/scoped_rerun_registry.json",
    "artifact_operational_index": "operations/artifact_operational_index.json",
    "import_preview_registry": "operator_imports/import_preview_registry.json",
    "validation_preview_registry": "operator_imports/validation_preview_registry.json",
    "reconciliation_preview_registry": "operator_imports/reconciliation_preview_registry.json",
    "operator_import_review_registry": "operator_imports/operator_import_review_registry.json",
    "performance_profile_registry": "performance/performance_profile_registry.json",
    "validation_timing_registry": "performance/validation_timing_registry.json",
    "rebuild_cost_registry": "performance/rebuild_cost_registry.json",
    "artifact_density_registry": "performance/artifact_density_registry.json",
    "dashboard_render_registry": "performance/dashboard_render_registry.json",
    "queue_scaling_registry": "performance/queue_scaling_registry.json",
    "throughput_analysis_registry": "performance/throughput_analysis_registry.json",
    "workload_heatmap_registry": "performance/workload_heatmap_registry.json",
    "scalability_warning_registry": "performance/scalability_warning_registry.json",
    "session_ergonomics_registry": "session_ergonomics/session_ergonomics_registry.json",
    "fatigue_reduction_registry": "session_ergonomics/fatigue_reduction_registry.json",
    "progressive_disclosure_registry": "session_ergonomics/progressive_disclosure_registry.json",
    "compact_navigation_registry": "session_ergonomics/compact_navigation_registry.json",
    "queue_chunking_registry": "session_ergonomics/queue_chunking_registry.json",
    "review_bookmark_registry": "session_ergonomics/review_bookmark_registry.json",
    "session_focus_restore_registry": "session_ergonomics/session_focus_restore_registry.json",
    "interruption_recovery_registry": "session_ergonomics/interruption_recovery_registry.json",
    "dense_dashboard_pagination_registry": "session_ergonomics/dense_dashboard_pagination_registry.json",
    "operator_attention_heatmap_registry": "session_ergonomics/operator_attention_heatmap_registry.json",
    "empirical_benchmark_history": "benchmarks/empirical_benchmark_history.json",
    "repeated_benchmark_snapshots": "benchmarks/repeated_benchmark_snapshots.json",
    "local_benchmark_baselines": "benchmarks/local_benchmark_baselines.json",
    "performance_drift_registry": "benchmarks/performance_drift_registry.json",
    "benchmark_comparison_history": "benchmarks/benchmark_comparison_history.json",
}


def operational_artifact(method: str) -> dict:
    artifact = base_artifact(status=STATUS_COMPLETE, method=method)
    artifact["limitations"] = [PHASE38_LIMITATION]
    return artifact


def build_generation_dependency_registry(output_dir: Path, outputs: dict) -> dict:
    rows = []
    for artifact, deps in sorted(DEPENDENCIES.items()):
        rows.append({
            "dependency_id": deterministic_id("GDEP", artifact, deps),
            "artifact": artifact,
            "artifact_ref": ARTIFACT_REFS.get(artifact),
            "dependencies": deps,
            "dependency_refs": [ARTIFACT_REFS.get(dep) or _infer_ref(dep) for dep in deps],
            "rebuild_scope": _scope_for(artifact),
            "dependency_aware_rebuild_required": bool(deps),
        })
    artifact = operational_artifact("deterministic_generation_dependency_tracker_v1")
    artifact.update({"generation_dependency_registry_id": deterministic_id("GDEPREG", [row["dependency_id"] for row in rows]), "dependencies": rows, "summary": {"dependency_entry_count": len(rows), "dependency_edge_count": sum(len(row["dependencies"]) for row in rows)}})
    return artifact


def _scope_for(name: str) -> str:
    if name.startswith("adjudication") or name.startswith("governance_escalation"):
        return "adjudication"
    if name.startswith("validation"):
        return "validation"
    return "operations"


def _infer_ref(name: str) -> str:
    if name in {"reviewer_adjudication_registry", "adjudication_lineage", "governance_conflict_analysis", "consensus_workflow_registry", "unresolved_ambiguity_registry"}:
        return f"adjudication/{name}.json"
    if name == "reconciliation_conflicts":
        return "reconciliation/reconciliation_conflicts.json"
    return f"{name}.json"
