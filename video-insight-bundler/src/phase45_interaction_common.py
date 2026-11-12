"""Shared deterministic Phase 45 static interaction helpers."""

from __future__ import annotations

from phase44_wayfinding_common import PHASE44_LIMITATION, graph_edges, source_ids, stable_row_id
from phase43_recall_common import RECALL_LENSES, events_for_focus, recall_source_events
from review_operational_common import compact_metrics, simple_review_page
from dashboard_layout import e

PHASE45_LIMITATION = PHASE44_LIMITATION

INTERACTION_PAGE_LINKS = [
    ("Wayfinding", "../wayfinding/operational_wayfinding_dashboard.html"),
    ("Sortable", "sortable_tables_dashboard.html"),
    ("Lenses", "dashboard_lenses_dashboard.html"),
    ("Routing", "compact_routing_dashboard.html"),
    ("Graph", "graph_navigation_dashboard.html"),
    ("Priority", "continuity_priority_dashboard.html"),
    ("Orphans", "orphan_remediation_dashboard.html"),
    ("Survivability", "route_survivability_dashboard.html"),
    ("Integrity", "dashboard_integrity_dashboard.html"),
    ("Compression", "interaction_compression_dashboard.html"),
    ("Pathways", "linked_review_pathways_dashboard.html"),
    ("Repair", "continuity_repair_dashboard.html"),
    ("Acceleration", "review_acceleration_dashboard.html"),
    ("Throughput", "throughput_indicator_dashboard.html"),
    ("Density", "high_density_interaction_dashboard.html"),
]

DASHBOARD_ROUTES = [
    ("recall", "../recall/historical_recall_dashboard.html"),
    ("wayfinding", "../wayfinding/operational_wayfinding_dashboard.html"),
    ("sortable", "sortable_tables_dashboard.html"),
    ("lenses", "dashboard_lenses_dashboard.html"),
    ("routing", "compact_routing_dashboard.html"),
    ("graph", "graph_navigation_dashboard.html"),
    ("priority", "continuity_priority_dashboard.html"),
    ("orphans", "orphan_remediation_dashboard.html"),
    ("survivability", "route_survivability_dashboard.html"),
    ("integrity", "dashboard_integrity_dashboard.html"),
    ("compression", "interaction_compression_dashboard.html"),
    ("pathways", "linked_review_pathways_dashboard.html"),
    ("repair", "continuity_repair_dashboard.html"),
    ("acceleration", "review_acceleration_dashboard.html"),
    ("throughput", "throughput_indicator_dashboard.html"),
    ("density", "high_density_interaction_dashboard.html"),
]


def phase45_artifact(method: str) -> dict:
    return {
        "analysis_status": "complete",
        "method": method,
        "phase": "45",
        "limitations": [PHASE45_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_operational_interaction": True,
        "deterministic_navigation_continuity": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "autonomous_remediation_used": False,
        "autonomous_editorial_decision_used": False,
        "human_review_required": True,
    }


def all_interaction_events(outputs: dict, limit: int = 96) -> list[dict]:
    return recall_source_events(outputs)[:limit]


def focus_specs() -> list[tuple[str, list[str]]]:
    return RECALL_LENSES


def focus_events(outputs: dict, focus: str, limit: int = 12) -> list[dict]:
    return events_for_focus(outputs, focus, limit)


def operational_score(row: dict) -> float:
    score = float(row.get("significance_score") or 0.0)
    focus = str(row.get("focus") or row.get("source_type") or "").lower()
    if "governance" in focus or "escalation" in focus:
        score += 0.2
    if "survivability" in focus or "regression" in focus:
        score += 0.15
    return round(min(1.0, score), 3)


def event_route_id(event_id: str | None) -> str:
    return stable_row_id("ROUTE", event_id or "missing")


def known_route_targets() -> set[str]:
    return {href for _label, href in DASHBOARD_ROUTES}


def route_rows() -> list[dict]:
    rows = []
    routes = DASHBOARD_ROUTES
    for index, (route_type, href) in enumerate(routes):
        next_href = routes[index + 1][1] if index + 1 < len(routes) else routes[0][1]
        rows.append(
            {
                "route_id": stable_row_id("IRTE", route_type, href, next_href),
                "route_type": route_type,
                "dashboard_href": href,
                "next_dashboard_href": next_href,
                "route_status": "complete",
                "survivability_signal": "reachable_static_relative_link",
                "human_review_required": True,
            }
        )
    return rows


def graph_node_ids(outputs: dict) -> set[str]:
    graph = outputs.get("narrative_linkage_graph_registry") or {}
    return {node.get("node_id") for node in graph.get("nodes") or [] if node.get("node_id")}


def graph_edge_rows(outputs: dict) -> list[dict]:
    return graph_edges(outputs)


def orphan_ids(outputs: dict) -> list[str]:
    orphan_rows = (outputs.get("orphaned_state_registry") or {}).get("orphaned_states") or []
    ids = [row.get("node_id") or row.get("source_event_id") or row.get("event_id") for row in orphan_rows]
    if ids:
        return sorted({item for item in ids if item})
    known = graph_node_ids(outputs)
    linked = set()
    for edge in graph_edge_rows(outputs):
        linked.add(edge.get("from_node_id"))
        linked.add(edge.get("to_node_id"))
    return sorted(item for item in known if item and item not in linked)


def render_static_table(rows: list[dict], fields: list[str], id_field: str) -> str:
    header = "".join(f"<th><button type='button' data-sort-key='{e(field)}'>{e(field.replace('_', ' ').title())}</button></th>" for field in fields)
    body = []
    for row in rows:
        cells = "".join(f"<td>{e(row.get(field))}</td>" for field in fields)
        body.append(f"<tr id='{e(row.get(id_field) or stable_row_id('ROW', row))}'>{cells}</tr>")
    script = """
<script>
document.querySelectorAll('[data-sort-key]').forEach(function(button) {
  button.addEventListener('click', function() {
    var table = button.closest('table');
    var column = Array.prototype.indexOf.call(button.closest('tr').children, button.closest('th'));
    var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
    rows.sort(function(a, b) { return a.children[column].innerText.localeCompare(b.children[column].innerText, undefined, {numeric: true}); });
    rows.forEach(function(row) { table.querySelector('tbody').appendChild(row); });
  });
});
</script>"""
    return f"<section class='panel'><table class='data-table'><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></section>{script}"


def render_lens_controls(lenses: list[str]) -> str:
    buttons = "".join(f"<button type='button' data-lens='{e(lens)}'>{e(lens.title())}</button>" for lens in lenses)
    return f"<section class='panel'><div class='toolbar'>{buttons}</div><p class='muted'>Static lens buttons expose deterministic focus labels for local review filtering.</p></section>"


def render_interaction_page(title: str, filename: str, rows: list[dict], fields: list[str], id_field: str, metrics: list[tuple[str, object]], lenses: list[str] | None = None) -> dict[str, str]:
    body = f"<section class='panel'><p>{e(PHASE45_LIMITATION)}</p></section>"
    if lenses:
        body += render_lens_controls(lenses)
    body += compact_metrics(metrics)
    body += render_static_table(rows, fields, id_field)
    return {filename: simple_review_page(title, "Static Interaction", filename, body, INTERACTION_PAGE_LINKS)}


def chain_from_events(rows: list[dict], prefix: str, route_type: str, limit: int = 8) -> list[dict]:
    selected = rows[:limit]
    chains = []
    for index, row in enumerate(selected):
        current_id = row.get("source_event_id")
        next_id = selected[index + 1].get("source_event_id") if index + 1 < len(selected) else None
        chains.append(
            {
                "continuity_route_id": stable_row_id(prefix, route_type, current_id, next_id or "terminal"),
                "route_type": route_type,
                "from_event_id": current_id,
                "to_event_id": next_id,
                "priority_score": operational_score(row),
                "route_status": "terminal" if next_id is None else "linked",
                "human_review_required": True,
            }
        )
    return chains
