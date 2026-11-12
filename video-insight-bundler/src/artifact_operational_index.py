"""Operational index for generated artifacts."""

from __future__ import annotations

from pathlib import Path

from dashboard_layout import e
from adjudication_event_import import PHASE38_LIMITATION
from generation_dependency_tracker import ARTIFACT_REFS, operational_artifact
from review_operational_common import card_grid, compact_metrics, simple_review_page
from stability import canonical_json, deterministic_id, sha256_text


def build_artifact_operational_index(output_dir: Path, outputs: dict, dependency_registry: dict | None = None) -> dict:
    deps = {row.get("artifact"): row for row in (dependency_registry or {}).get("dependencies") or []}
    rows = []
    for name, ref in sorted(ARTIFACT_REFS.items()):
        path = output_dir / ref
        exists = path.exists()
        digest = sha256_text(path.read_text(encoding="utf-8")) if exists and path.is_file() else None
        if digest is None and name in outputs:
            digest = sha256_text(canonical_json(outputs[name]))
            exists = True
        phase = 40 if name.startswith(("session_ergonomics", "fatigue_reduction", "progressive_disclosure", "compact_navigation", "queue_chunking", "review_bookmark", "session_focus_restore", "interruption_recovery", "dense_dashboard_pagination", "operator_attention_heatmap", "empirical_benchmark", "repeated_benchmark", "local_benchmark", "performance_drift", "benchmark_comparison_history")) else 39 if name.endswith("_registry") and (name.startswith(("import_preview", "validation_preview", "reconciliation_preview", "operator_import", "performance", "validation_timing", "rebuild_cost", "artifact_density", "dashboard_render", "queue_scaling", "throughput", "workload_heatmap", "scalability_warning"))) else 38 if name in ARTIFACT_REFS else None
        rows.append({
            "artifact_index_id": deterministic_id("AOP", name, ref, digest),
            "artifact": name,
            "artifact_ref": ref,
            "artifact_type": "json",
            "generation_phase": phase,
            "dependencies": (deps.get(name) or {}).get("dependencies", []),
            "validation_state": "pending_indexed_validation" if name.startswith("validation") else "generated" if exists else "planned",
            "rebuild_relevance": "direct" if exists else "planned",
            "last_regeneration": "deterministic_current_run" if exists else None,
            "artifact_hash": digest,
            "linked_dashboards": _linked_dashboards(name),
            "linked_schemas": [f"schemas/{name}.schema.json"],
        })
    artifact = operational_artifact("deterministic_artifact_operational_index_v1")
    artifact.update({"artifact_operational_index_id": deterministic_id("AOPREG", [row["artifact_index_id"] for row in rows]), "artifacts": rows, "summary": {"artifact_count": len(rows), "generated_artifact_count": sum(1 for row in rows if row["last_regeneration"])}})
    return artifact


def _linked_dashboards(name: str) -> list[str]:
    mapping = {
        "adjudication_event_registry": "visualizations/adjudication/adjudication_event_dashboard.html",
        "adjudication_history": "visualizations/adjudication/adjudication_history_dashboard.html",
        "adjudication_outcome_registry": "visualizations/adjudication/adjudication_outcome_dashboard.html",
        "governance_escalation_events": "visualizations/adjudication/governance_escalation_dashboard.html",
        "validation_index": "visualizations/operations/validation_index_dashboard.html",
        "selective_regeneration_registry": "visualizations/operations/selective_regeneration_dashboard.html",
        "scoped_rerun_registry": "visualizations/operations/scoped_rerun_dashboard.html",
        "artifact_operational_index": "visualizations/operations/artifact_operational_index_dashboard.html",
        "rebuild_manifest": "visualizations/operations/operational_scalability_dashboard.html",
        "import_preview_registry": "visualizations/operator/import_preview_dashboard.html",
        "validation_preview_registry": "visualizations/operator/validation_preview_dashboard.html",
        "reconciliation_preview_registry": "visualizations/operator/reconciliation_preview_dashboard.html",
        "operator_import_review_registry": "visualizations/operator/operator_import_dashboard.html",
        "performance_profile_registry": "visualizations/performance/performance_profile_dashboard.html",
        "validation_timing_registry": "visualizations/performance/validation_timing_dashboard.html",
        "rebuild_cost_registry": "visualizations/performance/rebuild_cost_dashboard.html",
        "artifact_density_registry": "visualizations/performance/artifact_density_dashboard.html",
        "dashboard_render_registry": "visualizations/performance/operational_observability_dashboard.html",
        "queue_scaling_registry": "visualizations/performance/queue_scaling_dashboard.html",
        "throughput_analysis_registry": "visualizations/performance/throughput_dashboard.html",
        "workload_heatmap_registry": "visualizations/performance/workload_heatmap_dashboard.html",
        "scalability_warning_registry": "visualizations/performance/scalability_warning_dashboard.html",
        "session_ergonomics_registry": "visualizations/ergonomics/session_ergonomics_dashboard.html",
        "fatigue_reduction_registry": "visualizations/ergonomics/fatigue_reduction_dashboard.html",
        "progressive_disclosure_registry": "visualizations/ergonomics/progressive_disclosure_dashboard.html",
        "compact_navigation_registry": "visualizations/ergonomics/compact_navigation_dashboard.html",
        "queue_chunking_registry": "visualizations/ergonomics/queue_chunking_dashboard.html",
        "interruption_recovery_registry": "visualizations/ergonomics/interruption_recovery_dashboard.html",
        "operator_attention_heatmap_registry": "visualizations/ergonomics/operator_attention_heatmap_dashboard.html",
        "empirical_benchmark_history": "visualizations/benchmarks/benchmark_history_dashboard.html",
        "repeated_benchmark_snapshots": "visualizations/benchmarks/repeated_benchmark_dashboard.html",
        "local_benchmark_baselines": "visualizations/benchmarks/empirical_baseline_dashboard.html",
        "performance_drift_registry": "visualizations/benchmarks/performance_drift_dashboard.html",
    }
    return [mapping[name]] if name in mapping else []


def render_operational_dashboards(outputs: dict) -> dict[str, str]:
    links = [
        ("Dashboard", "../dashboard.html"),
        ("Scalability", "operational_scalability_dashboard.html"),
        ("Validation Index", "validation_index_dashboard.html"),
        ("Selective Regeneration", "selective_regeneration_dashboard.html"),
        ("Scoped Rerun", "scoped_rerun_dashboard.html"),
        ("Artifact Index", "artifact_operational_index_dashboard.html"),
    ]
    limitation = f"<section class='panel'><p>{e(PHASE38_LIMITATION)}</p></section>"
    rebuilds = (outputs.get("rebuild_manifest") or {}).get("rebuild_entries") or []
    validations = (outputs.get("validation_index") or {}).get("validation_entries") or []
    regens = (outputs.get("selective_regeneration_registry") or {}).get("regeneration_scopes") or []
    reruns = (outputs.get("scoped_rerun_registry") or {}).get("scoped_reruns") or []
    artifacts = (outputs.get("artifact_operational_index") or {}).get("artifacts") or []
    return {
        "operational_scalability_dashboard.html": simple_review_page("Operational Scalability Dashboard", "Operations", "operational_scalability_dashboard.html", limitation + compact_metrics([("Rebuild entries", len(rebuilds)), ("Validation entries", len(validations)), ("Artifacts", len(artifacts))]) + card_grid(rebuilds, ["artifact", "rebuild_relevance", "validation_state", "selective_regeneration_allowed"], "rebuild_entry_id"), links),
        "validation_index_dashboard.html": simple_review_page("Validation Index Dashboard", "Operations", "validation_index_dashboard.html", limitation + card_grid(validations, ["artifact", "validation_scope", "validation_state", "cache_key"], "validation_index_id"), links),
        "selective_regeneration_dashboard.html": simple_review_page("Selective Regeneration Dashboard", "Operations", "selective_regeneration_dashboard.html", limitation + card_grid(regens, ["scope", "affected_artifacts", "explicit_decision_required", "hidden_mutable_state"], "selective_regeneration_id"), links),
        "scoped_rerun_dashboard.html": simple_review_page("Scoped Rerun Dashboard", "Operations", "scoped_rerun_dashboard.html", limitation + card_grid(reruns, ["scope", "rerun_mode", "dependency_aware", "safe_to_skip_unrelated_artifacts"], "scoped_rerun_id"), links),
        "artifact_operational_index_dashboard.html": simple_review_page("Artifact Operational Index Dashboard", "Operations", "artifact_operational_index_dashboard.html", limitation + card_grid(artifacts, ["artifact_ref", "generation_phase", "validation_state", "rebuild_relevance", "linked_dashboards"], "artifact_index_id"), links),
    }
