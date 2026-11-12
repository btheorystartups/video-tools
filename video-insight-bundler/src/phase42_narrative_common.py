"""Shared deterministic Phase 42 longitudinal narrative helpers."""

from __future__ import annotations

from dashboard_layout import e
from intelligence_common import base_artifact
from operator_workflow_common import risk_level, stable_row_id
from phase41_longitudinal_common import latest_lineage_entries
from review_operational_common import card_grid, compact_metrics, simple_review_page
from stability import STATUS_COMPLETE

PHASE42_LIMITATION = (
    "This system provides deterministic operational workflow and longitudinal observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, "
    "or make autonomous editorial decisions. Human review is required."
)

METRICS = [
    ("queue_total_count", "queue load"),
    ("operational_workload_units", "operational workload"),
    ("artifact_total_count", "artifact density"),
    ("rebuild_timing_seconds", "rebuild cost"),
    ("validation_timing_seconds", "validation cost"),
    ("dashboard_generation_seconds", "dashboard density"),
]


def phase42_artifact(method: str) -> dict:
    artifact = base_artifact(status=STATUS_COMPLETE, method=method)
    artifact["phase"] = "42"
    artifact["limitations"] = [PHASE42_LIMITATION]
    artifact["external_runtime_dependency_introduced"] = False
    artifact["hidden_mutable_runtime_state"] = False
    artifact["append_only_history_preserved"] = True
    artifact["nondeterministic_summarization_used"] = False
    return artifact


def narrative_links(active: str = "") -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Review", "longitudinal_review_dashboard.html"),
        ("Timeline", "narrative_timeline_dashboard.html"),
        ("Memory", "operator_memory_dashboard.html"),
        ("Changes", "change_explanation_dashboard.html"),
        ("Governance", "governance_evolution_dashboard.html"),
        ("Adjudication", "adjudication_evolution_dashboard.html"),
        ("Queue", "queue_evolution_dashboard.html"),
        ("Compression", "compressed_history_dashboard.html"),
        ("Drift", "drift_explanation_dashboard.html"),
        ("Significance", "historical_significance_dashboard.html"),
    ]


def render_narrative_page(title: str, filename: str, rows: list[dict], fields: list[str], id_field: str, metrics: list[tuple[str, object]]) -> dict[str, str]:
    body = f"<section class='panel'><p>{e(PHASE42_LIMITATION)}</p></section>" + compact_metrics(metrics) + card_grid(rows, fields, id_field)
    return {filename: simple_review_page(title, "Longitudinal Narratives", filename, body, narrative_links(filename))}


def lineage_deltas(outputs: dict) -> list[dict]:
    rows = []
    entries = latest_lineage_entries(outputs)
    for index, entry in enumerate(entries):
        previous = entries[index - 1] if index else {}
        for metric, label in METRICS:
            current = float(entry.get(metric) or 0)
            prior = float(previous.get(metric) or 0)
            delta = round(current - prior, 3)
            ratio = round(current / prior, 3) if prior else (1.0 if current else 0.0)
            direction = "increased" if delta > 0 else "decreased" if delta < 0 else "held steady"
            rows.append(
                {
                    "lineage_index": index,
                    "benchmark_run_id": entry.get("benchmark_run_id"),
                    "metric": metric,
                    "label": label,
                    "current_value": current,
                    "previous_value": prior,
                    "delta": delta,
                    "growth_ratio": ratio,
                    "direction": direction,
                    "significance_score": round(min(1.0, abs(delta) / max(1.0, abs(prior), abs(current))), 3),
                    "significance_level": risk_level(min(1.0, abs(delta) / max(1.0, abs(prior), abs(current)))),
                }
            )
    return rows


def top_deltas(outputs: dict, limit: int = 8) -> list[dict]:
    return sorted(lineage_deltas(outputs), key=lambda row: (-row["significance_score"], row["metric"], row["lineage_index"]))[:limit]


def reason_for_metric(metric: str, direction: str) -> str:
    reasons = {
        "queue_total_count": "queue-producing review, adjudication, reconciliation, governance, or escalation artifacts changed",
        "operational_workload_units": "queue load and rebuild timing changed in the benchmark lineage",
        "artifact_total_count": "generated artifact counts changed in the benchmark lineage",
        "rebuild_timing_seconds": "local rebuild timing changed in the benchmark lineage",
        "validation_timing_seconds": "local validation timing changed in the benchmark lineage",
        "dashboard_generation_seconds": "dashboard generation timing changed in the benchmark lineage",
    }
    prefix = "because" if direction != "held steady" else "because the tracked inputs remained stable:"
    return f"{prefix} {reasons.get(metric, 'the tracked deterministic source metric changed')}"


def deterministic_sentence(row: dict) -> str:
    return (
        f"{row['label'].title()} {row['direction']} from {row['previous_value']} to {row['current_value']} "
        f"for run {row.get('benchmark_run_id') or 'unknown'}; {reason_for_metric(row['metric'], row['direction'])}."
    )


def base_registry_id(prefix: str, rows: list[dict], id_field: str) -> str:
    return stable_row_id(prefix, [row.get(id_field) for row in rows])


def governance_rows(outputs: dict) -> list[dict]:
    return (outputs.get("governance_drift_analysis") or {}).get("governance_drift_entries") or []


def adjudication_rows(outputs: dict) -> list[dict]:
    rows = []
    for key, field in [
        ("adjudication_queue_registry", "queue_items"),
        ("adjudication_history", "history_entries"),
        ("governance_escalation_events", "escalation_events"),
        ("reviewer_adjudication_registry", "adjudications"),
    ]:
        for index, item in enumerate((outputs.get(key) or {}).get(field) or []):
            rows.append({"source_registry": key, "source_index": index, "source_id": item.get("queue_item_id") or item.get("adjudication_id") or item.get("escalation_event_id") or item.get("history_entry_id")})
    return rows


def queue_rows(outputs: dict) -> list[dict]:
    rows = []
    for key in ["review_queue_registry", "adjudication_queue_registry", "unresolved_conflict_queue", "reconciliation_required_queue", "governance_review_queue", "escalation_required_queue"]:
        for index, item in enumerate((outputs.get(key) or {}).get("queue_items") or []):
            rows.append({"source_registry": key, "source_index": index, "source_id": item.get("queue_item_id")})
    return rows
