"""Shared deterministic Phase 44 recall wayfinding helpers."""

from __future__ import annotations

from phase43_recall_common import PHASE43_LIMITATION, RECALL_LENSES, events_for_focus, recall_source_events, stable_row_id
from review_operational_common import card_grid, compact_metrics, simple_review_page
from dashboard_layout import e

PHASE44_LIMITATION = PHASE43_LIMITATION

WAYFINDING_PAGE_LINKS = [
    ("Recall", "../recall/historical_recall_dashboard.html"),
    ("Layered", "layered_recall_dashboard.html"),
    ("Breadcrumbs", "operational_breadcrumb_dashboard.html"),
    ("Cross Highlight", "graph_crosshighlight_dashboard.html"),
    ("Sync", "continuity_sync_dashboard.html"),
    ("Pagination", "history_pagination_dashboard.html"),
    ("Grouping", "compressed_node_grouping_dashboard.html"),
    ("Filtered", "filtered_continuity_dashboard.html"),
    ("Scope", "historical_scope_dashboard.html"),
    ("Completeness", "navigation_completeness_dashboard.html"),
    ("Orphans", "orphaned_state_dashboard.html"),
    ("Path Validation", "continuity_validation_dashboard.html"),
    ("Wayfinding", "operational_wayfinding_dashboard.html"),
    ("Deep Links", "contextual_deep_link_dashboard.html"),
    ("Survivability", "navigation_survivability_dashboard.html"),
]


def phase44_artifact(method: str) -> dict:
    return {
        "analysis_status": "complete",
        "method": method,
        "phase": "44",
        "limitations": [PHASE44_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_navigation_continuity": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "autonomous_prioritization_used": False,
        "human_review_required": True,
    }


def render_wayfinding_page(title: str, filename: str, rows: list[dict], fields: list[str], id_field: str, metrics: list[tuple[str, object]]) -> dict[str, str]:
    body = f"<section class='panel'><p>{e(PHASE44_LIMITATION)}</p></section>" + compact_metrics(metrics) + card_grid(rows, fields, id_field)
    return {filename: simple_review_page(title, "Recall Wayfinding", filename, body, WAYFINDING_PAGE_LINKS)}


def all_wayfinding_events(outputs: dict, limit: int = 48) -> list[dict]:
    return recall_source_events(outputs)[:limit]


def focus_specs() -> list[tuple[str, list[str]]]:
    return RECALL_LENSES


def source_ids(rows: list[dict]) -> list[str]:
    return [row.get("source_event_id") or row.get("node_id") or row.get("event_id") for row in rows if row.get("source_event_id") or row.get("node_id") or row.get("event_id")]


def event_id_set(outputs: dict) -> set[str]:
    ids = {row.get("source_event_id") for row in all_wayfinding_events(outputs) if row.get("source_event_id")}
    graph = outputs.get("narrative_linkage_graph_registry") or {}
    ids.update(node.get("node_id") for node in graph.get("nodes") or [] if node.get("node_id"))
    return ids


def graph_edges(outputs: dict) -> list[dict]:
    return list((outputs.get("narrative_linkage_graph_registry") or {}).get("edges") or [])


def path_for_focus(outputs: dict, focus: str, limit: int = 6) -> list[dict]:
    return events_for_focus(outputs, focus, limit)


def continuity_pairs(rows: list[dict], prefix: str, relation_type: str) -> list[dict]:
    pairs = []
    for index, row in enumerate(rows):
        next_row = rows[index + 1] if index + 1 < len(rows) else None
        pairs.append(
            {
                "continuity_path_id": stable_row_id(prefix, row.get("source_event_id"), next_row.get("source_event_id") if next_row else "terminal"),
                "from_event_id": row.get("source_event_id"),
                "to_event_id": next_row.get("source_event_id") if next_row else None,
                "relation_type": relation_type,
                "path_status": "terminal" if next_row is None else "linked",
                "human_review_required": True,
            }
        )
    return pairs
