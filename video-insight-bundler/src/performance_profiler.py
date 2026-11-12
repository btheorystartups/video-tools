"""Corpus-scale deterministic performance profiling."""

from __future__ import annotations

from operator_workflow_common import deterministic_cost, performance_links, phase39_artifact, render_registry_page, stable_row_id


def build_performance_profile_registry(outputs: dict) -> dict:
    validation_count = len((outputs.get("validation_index") or {}).get("validation_entries") or [])
    dashboards = len((outputs.get("dashboard_render_registry") or {}).get("render_entries") or [])
    queues = sum(len((outputs.get(key) or {}).get("queue_items") or []) for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue"])
    conflicts = len((outputs.get("reconciliation_conflicts") or {}).get("conflicts") or [])
    adjudications = len((outputs.get("adjudication_event_registry") or {}).get("events") or [])
    specs = [
        ("artifact_generation", validation_count + dashboards, 0.006),
        ("validation", validation_count, 0.004),
        ("dashboard_rendering", dashboards, 0.01),
        ("queue_generation", queues, 0.003),
        ("reconciliation", conflicts, 0.012),
        ("adjudication_processing", adjudications, 0.008),
    ]
    rows = []
    for profile_type, units, scale in specs:
        rows.append({
            "performance_profile_id": stable_row_id("PERF", profile_type, units),
            "profile_type": profile_type,
            "input_units": units,
            "estimated_seconds": deterministic_cost(units, base=0.01, scale=scale),
            "measurement_mode": "deterministic_complexity_estimate",
            "nondeterministic_profiling_used": False,
        })
    artifact = phase39_artifact("deterministic_performance_profiler_v1")
    artifact.update({"performance_profile_registry_id": stable_row_id("PERFREG", [row["performance_profile_id"] for row in rows]), "profile_entries": rows, "summary": {"profile_entry_count": len(rows), "estimated_total_seconds": round(sum(row["estimated_seconds"] for row in rows), 3)}})
    return artifact


def render_performance_dashboards(outputs: dict) -> dict[str, str]:
    links = performance_links("")
    specs = {
        "operational_observability_dashboard.html": ("Operational Observability Dashboard", (outputs.get("operational_observability_registry") or {}).get("observability_entries") or [], ["signal", "value", "status", "operator_relevance"], "observability_id"),
        "performance_profile_dashboard.html": ("Performance Profile Dashboard", (outputs.get("performance_profile_registry") or {}).get("profile_entries") or [], ["profile_type", "input_units", "estimated_seconds", "measurement_mode"], "performance_profile_id"),
        "validation_timing_dashboard.html": ("Validation Timing Dashboard", (outputs.get("validation_timing_registry") or {}).get("timing_entries") or [], ["artifact", "validation_scope", "estimated_validation_seconds", "cache_reusable"], "validation_timing_id"),
        "rebuild_cost_dashboard.html": ("Rebuild Cost Dashboard", (outputs.get("rebuild_cost_registry") or {}).get("rebuild_costs") or [], ["artifact", "estimated_regeneration_count", "dependency_chain_depth", "estimated_cost_units"], "rebuild_cost_id"),
        "artifact_density_dashboard.html": ("Artifact Density Dashboard", (outputs.get("artifact_density_registry") or {}).get("density_entries") or [], ["artifact_area", "artifact_count", "dashboard_link_count", "density_class"], "artifact_density_id"),
        "queue_scaling_dashboard.html": ("Queue Scaling Dashboard", (outputs.get("queue_scaling_registry") or {}).get("simulations") or [], ["simulated_queue_items", "generation_impact_units", "dashboard_density_units", "scaling_risk"], "queue_scaling_id"),
        "throughput_dashboard.html": ("Throughput Dashboard", (outputs.get("throughput_analysis_registry") or {}).get("throughput_entries") or [], ["workflow", "backlog_items", "heuristic_items_per_hour", "estimated_operator_hours"], "throughput_analysis_id"),
        "workload_heatmap_dashboard.html": ("Workload Heatmap Dashboard", (outputs.get("workload_heatmap_registry") or {}).get("heatmap_cells") or [], ["dimension", "density_count", "density_score", "density_class"], "workload_heatmap_id"),
        "scalability_warning_dashboard.html": ("Scalability Warning Dashboard", (outputs.get("scalability_warning_registry") or {}).get("warnings") or [], ["warning_type", "risk_level", "evidence_count", "operator_action"], "scalability_warning_id"),
    }
    rendered = {}
    for filename, (title, rows, fields, id_field) in specs.items():
        rendered[filename] = render_registry_page(title, "Performance", filename, rows, fields, id_field, [("Rows", len(rows))], links)
    return rendered
