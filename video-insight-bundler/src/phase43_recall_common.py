"""Shared deterministic Phase 43 narrative navigation helpers."""

from __future__ import annotations

from dashboard_layout import e
from operator_workflow_common import risk_level, stable_row_id
from phase42_narrative_common import deterministic_sentence, lineage_deltas, phase42_artifact, top_deltas
from review_operational_common import card_grid, compact_metrics, simple_review_page

PHASE43_LIMITATION = (
    "This system provides deterministic operational workflow and longitudinal observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, predict viewer behavior, "
    "or make autonomous editorial decisions. Human review is required."
)

RECALL_LENSES = [
    ("governance", ["governance", "blocker", "conflict"]),
    ("escalation", ["escalation", "adjudication"]),
    ("survivability", ["survivability", "completion", "review"]),
    ("ambiguity", ["ambiguity", "disagreement", "conflict"]),
    ("workload", ["queue", "workload", "artifact", "rebuild", "validation"]),
    ("throughput", ["throughput", "timing", "dashboard", "rebuild"]),
]


def phase43_artifact(method: str) -> dict:
    artifact = phase42_artifact(method)
    artifact["phase"] = "43"
    artifact["limitations"] = [PHASE43_LIMITATION]
    artifact["historical_navigation_enabled"] = True
    artifact["operator_handoff_continuity_enabled"] = True
    artifact["autonomous_interpretation_used"] = False
    return artifact


def recall_links(active: str = "") -> list[tuple[str, str]]:
    return [
        ("Narratives", "../narratives/longitudinal_review_dashboard.html"),
        ("Recall", "historical_recall_dashboard.html"),
        ("Handoff", "operator_handoff_dashboard.html"),
        ("Lenses", "historical_lens_dashboard.html"),
        ("Stitching", "contextual_stitching_dashboard.html"),
        ("Milestones", "milestone_continuity_dashboard.html"),
        ("Escalation", "escalation_continuity_dashboard.html"),
        ("Governance", "governance_continuity_dashboard.html"),
        ("Related", "related_event_dashboard.html"),
        ("Restore", "rapid_context_restore_dashboard.html"),
        ("Memory", "operational_memory_dashboard.html"),
        ("Graph", "narrative_linkage_dashboard.html"),
        ("Continuity", "continuity_panel_dashboard.html"),
        ("Transitions", "operational_transition_dashboard.html"),
        ("Compressed", "compressed_recall_dashboard.html"),
    ]


def render_recall_page(title: str, filename: str, rows: list[dict], fields: list[str], id_field: str, metrics: list[tuple[str, object]]) -> dict[str, str]:
    body = f"<section class='panel'><p>{e(PHASE43_LIMITATION)}</p></section>" + compact_metrics(metrics) + card_grid(rows, fields, id_field)
    return {filename: simple_review_page(title, "Recall Navigation", filename, body, recall_links(filename))}


def recall_source_events(outputs: dict) -> list[dict]:
    events = []
    for row in top_deltas(outputs, 18):
        events.append(
            {
                "source_event_id": stable_row_id("REVT", "delta", row["metric"], row["lineage_index"], row["delta"]),
                "source_type": row["metric"],
                "focus": focus_for_metric(row["metric"]),
                "lineage_index": row["lineage_index"],
                "benchmark_run_id": row.get("benchmark_run_id"),
                "summary": deterministic_sentence(row),
                "significance_score": row["significance_score"],
                "significance_level": row["significance_level"],
                "source_ref": row.get("benchmark_run_id"),
            }
        )
    for key, field, focus in [
        ("governance_drift_analysis", "governance_drift_entries", "governance"),
        ("operational_milestone_registry", "milestones", "milestone"),
        ("historical_significance_registry", "significance_events", "historical_significance"),
        ("operator_memory_restore_registry", "memory_items", "handoff"),
        ("review_survivability_analysis", "survivability_entries", "survivability"),
        ("operational_regression_registry", "regressions", "regression"),
        ("escalation_trend_analysis", "escalation_entries", "escalation"),
        ("ambiguity_accumulation", "ambiguity_entries", "ambiguity"),
    ]:
        for index, item in enumerate((outputs.get(key) or {}).get(field) or []):
            event_id = item.get("operational_milestone_id") or item.get("historical_significance_id") or item.get("operator_memory_restore_id") or item.get("regression_id") or item.get("source_event_id") or stable_row_id("REVT", key, index)
            events.append(
                {
                    "source_event_id": event_id,
                    "source_type": key,
                    "focus": focus,
                    "lineage_index": item.get("lineage_index", index),
                    "benchmark_run_id": item.get("benchmark_run_id"),
                    "summary": item.get("description") or item.get("event_summary") or item.get("restored_context") or item.get("summary") or key.replace("_", " "),
                    "significance_score": float(item.get("significance_score") or item.get("severity_score") or 0.5),
                    "significance_level": item.get("significance_level") or risk_level(float(item.get("significance_score") or 0.5)),
                    "source_ref": item.get("append_only_lineage_ref") or item.get("benchmark_run_id") or event_id,
                }
            )
    deduped = {row["source_event_id"]: row for row in events}
    return sorted(deduped.values(), key=lambda row: (-row["significance_score"], str(row["focus"]), str(row["source_event_id"])))


def focus_for_metric(metric: str) -> str:
    text = metric.lower()
    for lens, keywords in RECALL_LENSES:
        if any(keyword in text for keyword in keywords):
            return lens
    return "operational"


def events_for_focus(outputs: dict, focus: str, limit: int = 8) -> list[dict]:
    keywords = dict(RECALL_LENSES).get(focus, [focus])
    rows = [
        row
        for row in recall_source_events(outputs)
        if row.get("focus") == focus or any(keyword in (row.get("source_type") or "").lower() or keyword in (row.get("summary") or "").lower() for keyword in keywords)
    ]
    return rows[:limit]


def source_ids(rows: list[dict]) -> list[str]:
    return [row.get("source_event_id") for row in rows if row.get("source_event_id")]


def relation_rows(outputs: dict, relation_type: str, focus: str, limit: int = 8) -> list[dict]:
    rows = events_for_focus(outputs, focus, limit)
    links = []
    for index, row in enumerate(rows):
        next_row = rows[index + 1] if index + 1 < len(rows) else None
        links.append(
            {
                "relation_id": stable_row_id("RLNK", relation_type, row.get("source_event_id"), next_row.get("source_event_id") if next_row else "terminal"),
                "relation_type": relation_type,
                "focus": focus,
                "from_event_id": row.get("source_event_id"),
                "to_event_id": next_row.get("source_event_id") if next_row else None,
                "summary": row.get("summary"),
                "navigation_hint": "continue_to_related_event" if next_row else "terminal_recall_point",
                "human_review_required": True,
            }
        )
    return links


def transition_rows(outputs: dict, limit: int = 12) -> list[dict]:
    rows = []
    deltas = sorted(lineage_deltas(outputs), key=lambda row: (row["lineage_index"], row["metric"]))[:limit]
    for row in deltas:
        rows.append(
            {
                "transition_id": stable_row_id("OST", row["metric"], row["lineage_index"], row["previous_value"], row["current_value"]),
                "transition_type": focus_for_metric(row["metric"]),
                "lineage_index": row["lineage_index"],
                "from_value": row["previous_value"],
                "to_value": row["current_value"],
                "direction": row["direction"],
                "summary": deterministic_sentence(row),
                "source_ref": row.get("benchmark_run_id"),
                "human_review_required": True,
            }
        )
    return rows
