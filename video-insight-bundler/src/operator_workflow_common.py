"""Shared Phase 39 operator workflow and profiling helpers."""

from __future__ import annotations

from dashboard_layout import e
from intelligence_common import base_artifact, clamp, num
from review_operational_common import card_grid, compact_metrics, simple_review_page
from stability import STATUS_COMPLETE, deterministic_id

PHASE39_LIMITATION = (
    "This system provides deterministic operational workflow and performance observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, "
    "or make autonomous editorial decisions. Human review is required."
)

PHASE40_LIMITATION = PHASE39_LIMITATION


def phase39_artifact(method: str) -> dict:
    artifact = base_artifact(status=STATUS_COMPLETE, method=method)
    artifact["limitations"] = [PHASE39_LIMITATION]
    artifact["external_runtime_dependency_introduced"] = False
    artifact["hidden_mutable_runtime_state"] = False
    return artifact


def phase40_artifact(method: str) -> dict:
    artifact = phase39_artifact(method)
    artifact["phase"] = "40"
    return artifact


def deterministic_cost(*values: object, base: float = 0.05, scale: float = 0.01) -> float:
    total = sum(num(value) for value in values)
    return round(base + (total * scale), 3)


def risk_level(score: float) -> str:
    value = clamp(score)
    if value >= 0.75:
        return "high"
    if value >= 0.45:
        return "medium"
    return "low"


def operator_links(active: str) -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Operator Import", "operator_import_dashboard.html"),
        ("Import Preview", "import_preview_dashboard.html"),
        ("Validation Preview", "validation_preview_dashboard.html"),
        ("Reconciliation Preview", "reconciliation_preview_dashboard.html"),
    ]


def performance_links(active: str) -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Observability", "operational_observability_dashboard.html"),
        ("Performance", "performance_profile_dashboard.html"),
        ("Validation Timing", "validation_timing_dashboard.html"),
        ("Rebuild Cost", "rebuild_cost_dashboard.html"),
        ("Artifact Density", "artifact_density_dashboard.html"),
        ("Queue Scaling", "queue_scaling_dashboard.html"),
        ("Throughput", "throughput_dashboard.html"),
        ("Heatmap", "workload_heatmap_dashboard.html"),
        ("Warnings", "scalability_warning_dashboard.html"),
    ]


def ergonomics_links(active: str) -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Session", "session_ergonomics_dashboard.html"),
        ("Fatigue", "fatigue_reduction_dashboard.html"),
        ("Navigation", "compact_navigation_dashboard.html"),
        ("Disclosure", "progressive_disclosure_dashboard.html"),
        ("Queue Chunks", "queue_chunking_dashboard.html"),
        ("Recovery", "interruption_recovery_dashboard.html"),
        ("Attention", "operator_attention_heatmap_dashboard.html"),
    ]


def benchmark_links(active: str) -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("History", "benchmark_history_dashboard.html"),
        ("Drift", "performance_drift_dashboard.html"),
        ("Baselines", "empirical_baseline_dashboard.html"),
        ("Snapshots", "repeated_benchmark_dashboard.html"),
    ]


def limitation_panel() -> str:
    return f"<section class='panel'><p>{e(PHASE39_LIMITATION)}</p></section>"


def render_registry_page(title: str, section: str, active: str, rows: list[dict], fields: list[str], id_field: str, metrics: list[tuple[str, object]], links: list[tuple[str, str]]) -> str:
    body = limitation_panel() + compact_metrics(metrics) + card_grid(rows, fields, id_field)
    return simple_review_page(title, section, active, body, links)


def stable_row_id(prefix: str, *parts: object) -> str:
    return deterministic_id(prefix, *parts)
