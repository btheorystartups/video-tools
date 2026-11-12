"""Shared deterministic Phase 41 longitudinal operational helpers."""

from __future__ import annotations

from dashboard_layout import e
from intelligence_common import base_artifact
from operator_workflow_common import risk_level, stable_row_id
from review_operational_common import card_grid, compact_metrics, simple_review_page
from stability import STATUS_COMPLETE

PHASE41_LIMITATION = (
    "This system provides deterministic operational workflow and longitudinal observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, "
    "or make autonomous editorial decisions. Human review is required."
)


def phase41_artifact(method: str) -> dict:
    artifact = base_artifact(status=STATUS_COMPLETE, method=method)
    artifact["phase"] = "41"
    artifact["limitations"] = [PHASE41_LIMITATION]
    artifact["external_runtime_dependency_introduced"] = False
    artifact["hidden_mutable_runtime_state"] = False
    artifact["append_only_history_preserved"] = True
    return artifact


def longitudinal_links(active: str = "") -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Lineage", "benchmark_lineage_dashboard.html"),
        ("Sessions", "cross_session_analytics_dashboard.html"),
        ("Trends", "operational_trend_dashboard.html"),
        ("Governance", "governance_drift_dashboard.html"),
        ("Workload", "workload_evolution_dashboard.html"),
        ("Regressions", "operational_regression_dashboard.html"),
        ("Heatmap", "longitudinal_heatmap_dashboard.html"),
    ]


def render_longitudinal_page(title: str, filename: str, rows: list[dict], fields: list[str], id_field: str, metrics: list[tuple[str, object]]) -> dict[str, str]:
    body = f"<section class='panel'><p>{e(PHASE41_LIMITATION)}</p></section>" + compact_metrics(metrics) + card_grid(rows, fields, id_field)
    return {filename: simple_review_page(title, "Longitudinal", filename, body, longitudinal_links(filename))}


def count_rows(outputs: dict, key: str, *fields: str) -> int:
    data = outputs.get(key) or {}
    for field in fields:
        rows = data.get(field)
        if isinstance(rows, list):
            return len(rows)
    return 0


def queue_count(outputs: dict) -> int:
    keys = [
        "review_queue_registry",
        "adjudication_queue_registry",
        "unresolved_conflict_queue",
        "reconciliation_required_queue",
        "imported_review_followup_queue",
        "governance_review_queue",
        "escalation_required_queue",
    ]
    return sum(count_rows(outputs, key, "queue_items", "items") for key in keys)


def escalation_count(outputs: dict) -> int:
    return count_rows(outputs, "governance_escalation_events", "escalation_events") + count_rows(outputs, "review_escalation_registry", "escalation_items")


def ambiguity_count(outputs: dict) -> int:
    return count_rows(outputs, "unresolved_ambiguity_registry", "ambiguities") + count_rows(outputs, "reviewer_disagreement_registry", "disagreements")


def governance_pressure(outputs: dict) -> int:
    return (
        count_rows(outputs, "governance_conflict_analysis", "governance_conflicts")
        + count_rows(outputs, "blocker_analysis", "blockers")
        + count_rows(outputs, "governance_review_queue", "queue_items")
    )


def latest_lineage_entries(outputs: dict) -> list[dict]:
    return (outputs.get("persistent_benchmark_lineage") or {}).get("lineage_entries") or []


def trend_rows_from_lineage(entries: list[dict], metric: str, row_prefix: str, trend_type: str) -> list[dict]:
    rows = []
    previous = None
    for index, entry in enumerate(entries):
        current = float(entry.get(metric) or 0)
        delta = round(current - previous, 3) if previous is not None else 0.0
        ratio = round(current / previous, 3) if previous else (1.0 if current else 0.0)
        rows.append(
            {
                f"{row_prefix}_id": stable_row_id(row_prefix.upper(), trend_type, index, entry.get("benchmark_run_id"), current, previous),
                "trend_type": trend_type,
                "lineage_index": index,
                "benchmark_run_id": entry.get("benchmark_run_id"),
                "metric": metric,
                "current_value": current,
                "previous_value": previous if previous is not None else 0.0,
                "delta": delta,
                "growth_ratio": ratio,
                "trend_level": risk_level(min(1.0, max(0.0, ratio - 1.0))),
                "human_review_required": True,
            }
        )
        previous = current
    return rows
