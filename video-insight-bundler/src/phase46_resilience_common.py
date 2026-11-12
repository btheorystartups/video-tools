"""Shared deterministic Phase 46 resilience and accessibility helpers."""

from __future__ import annotations

from dashboard_layout import e
from phase45_interaction_common import DASHBOARD_ROUTES, all_interaction_events, graph_edge_rows, route_rows, stable_row_id
from review_operational_common import compact_metrics, simple_review_page

PHASE46_LIMITATION = (
    "This system provides deterministic operational workflow and longitudinal observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, "
    "predict viewer behavior, or make autonomous editorial decisions. Human review is required."
)

RESILIENCE_PAGE_LINKS = [
    ("Interaction", "../interaction/high_density_interaction_dashboard.html"),
    ("Keyboard", "keyboard_navigation_dashboard.html"),
    ("Shortcuts", "operational_shortcuts_dashboard.html"),
    ("Focus", "focus_survivability_dashboard.html"),
    ("Accessibility", "accessibility_validation_dashboard.html"),
    ("Screen Reader", "screenreader_structure_dashboard.html"),
    ("Headings", "heading_hierarchy_dashboard.html"),
    ("Stress", "large_history_stress_dashboard.html"),
    ("Deep Links", "deep_link_survivability_dashboard.html"),
    ("Pagination", "pagination_endurance_dashboard.html"),
    ("Fatigue", "navigation_fatigue_dashboard.html"),
    ("Traversal", "accessibility_traversal_dashboard.html"),
    ("Endurance", "operational_endurance_dashboard.html"),
    ("Route Stress", "continuity_route_stress_dashboard.html"),
    ("Dashboard", "dashboard_survivability_dashboard.html"),
    ("Resilience", "interaction_resilience_dashboard.html"),
]


def phase46_artifact(method: str) -> dict:
    return {
        "analysis_status": "complete",
        "method": method,
        "phase": "46",
        "limitations": [PHASE46_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_operational_interaction": True,
        "deterministic_keyboard_navigation": True,
        "deterministic_accessibility_validation": True,
        "deterministic_navigation_continuity": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "autonomous_remediation_used": False,
        "autonomous_editorial_decision_used": False,
        "human_review_required": True,
    }


def resilience_events(outputs: dict, limit: int = 128) -> list[dict]:
    return all_interaction_events(outputs, limit)


def resilience_routes() -> list[dict]:
    return route_rows()


def route_count() -> int:
    return len(DASHBOARD_ROUTES)


def continuity_edge_count(outputs: dict) -> int:
    return len(graph_edge_rows(outputs))


def bounded_score(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 1.0
    return round(max(0.0, min(1.0, numerator / denominator)), 3)


def render_resilience_table(rows: list[dict], fields: list[str], id_field: str) -> str:
    header = "".join(f"<th scope='col'>{e(field.replace('_', ' ').title())}</th>" for field in fields)
    body = []
    for row in rows:
        cells = "".join(f"<td>{e(row.get(field))}</td>" for field in fields)
        body.append(f"<tr id='{e(row.get(id_field) or stable_row_id('RROW', row))}' tabindex='-1'>{cells}</tr>")
    return f"<section class='panel'><table class='data-table'><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></section>"


def render_resilience_page(
    title: str,
    filename: str,
    rows: list[dict],
    fields: list[str],
    id_field: str,
    metrics: list[tuple[str, object]],
    extra: str = "",
) -> dict[str, str]:
    shortcut_panel = (
        "<section class='panel' aria-labelledby='keyboard-hints'><h2 id='keyboard-hints'>Keyboard Hints</h2>"
        "<p class='muted'>Use dashboard jump links, table row anchors, and focus restore entries as deterministic local navigation aids.</p></section>"
    )
    body = f"<section class='panel'><p>{e(PHASE46_LIMITATION)}</p></section>{shortcut_panel}{extra}"
    body += compact_metrics(metrics)
    body += render_resilience_table(rows, fields, id_field)
    return {filename: simple_review_page(title, "Operational Resilience", filename, body, RESILIENCE_PAGE_LINKS)}
