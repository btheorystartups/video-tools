"""Shared deterministic Phase 47 replay and continuity proof helpers."""

from __future__ import annotations

from dashboard_layout import e
from phase45_interaction_common import graph_edge_rows, route_rows, stable_row_id
from phase46_resilience_common import bounded_score, resilience_events
from review_operational_common import compact_metrics, simple_review_page

PHASE47_LIMITATION = (
    "This system provides deterministic operational workflow and longitudinal observability support. "
    "It does not autonomously resolve reviewer disagreements, infer identity, diagnose emotion, "
    "predict viewer behavior, or make autonomous editorial decisions. Human review is required."
)

REPLAY_PAGE_LINKS = [
    ("Resilience", "../resilience/interaction_resilience_dashboard.html"),
    ("Replay", "deterministic_replay_dashboard.html"),
    ("Continuity", "continuity_replay_dashboard.html"),
    ("Breadcrumb", "breadcrumb_replay_dashboard.html"),
    ("Routes", "route_reproducibility_dashboard.html"),
    ("Traversal", "traversal_fixture_dashboard.html"),
    ("Extreme", "extreme_history_dashboard.html"),
    ("Graph", "continuity_graph_dashboard.html"),
    ("Semantics", "accessibility_semantic_dashboard.html"),
    ("ARIA", "aria_survivability_dashboard.html"),
    ("Integrity", "continuity_integrity_dashboard.html"),
    ("Coverage", "replay_coverage_dashboard.html"),
    ("Survivability", "replay_survivability_dashboard.html"),
    ("Score", "history_reproducibility_dashboard.html"),
    ("Proof", "operational_proof_dashboard.html"),
    ("Navigation", "deterministic_navigation_dashboard.html"),
]


def phase47_artifact(method: str) -> dict:
    return {
        "analysis_status": "complete",
        "method": method,
        "phase": "47",
        "limitations": [PHASE47_LIMITATION],
        "append_only_history_preserved": True,
        "deterministic_operational_replay": True,
        "deterministic_navigation_verification": True,
        "deterministic_continuity_proofing": True,
        "browserless_replay_validation": True,
        "external_runtime_dependency_introduced": False,
        "hidden_mutable_runtime_state_introduced": False,
        "autonomous_remediation_used": False,
        "autonomous_editorial_decision_used": False,
        "human_review_required": True,
    }


def replay_routes() -> list[dict]:
    return route_rows()


def replay_events(outputs: dict, limit: int = 160) -> list[dict]:
    return resilience_events(outputs, limit)


def replay_edges(outputs: dict) -> list[dict]:
    return graph_edge_rows(outputs)


def replay_breadcrumbs(outputs: dict) -> list[dict]:
    return (outputs.get("operational_breadcrumb_registry") or {}).get("breadcrumbs") or []


def replay_sequences(outputs: dict, limit: int = 24) -> list[dict]:
    events = replay_events(outputs, limit)
    routes = replay_routes()
    rows = []
    for index, event in enumerate(events):
        route = routes[index % len(routes)] if routes else {}
        previous_id = events[index - 1].get("source_event_id") if index else None
        next_id = events[index + 1].get("source_event_id") if index + 1 < len(events) else None
        rows.append(
            {
                "sequence_id": stable_row_id("RSEQ", index, event.get("source_event_id"), route.get("route_id")),
                "sequence_order": index + 1,
                "source_event_id": event.get("source_event_id"),
                "previous_event_id": previous_id,
                "next_event_id": next_id,
                "dashboard_href": route.get("dashboard_href"),
                "route_id": route.get("route_id"),
                "replay_step_type": "terminal" if next_id is None else "linked_step",
                "replay_status": "replayable_static",
                "human_review_required": True,
            }
        )
    if not rows:
        for index, route in enumerate(routes[:8]):
            rows.append(
                {
                    "sequence_id": stable_row_id("RSEQ", "route", route.get("route_id")),
                    "sequence_order": index + 1,
                    "source_event_id": None,
                    "previous_event_id": None,
                    "next_event_id": None,
                    "dashboard_href": route.get("dashboard_href"),
                    "route_id": route.get("route_id"),
                    "replay_step_type": "route_only",
                    "replay_status": "replayable_static",
                    "human_review_required": True,
                }
            )
    return rows


def continuity_chain_rows(outputs: dict, limit: int = 80) -> list[dict]:
    rows = []
    for edge in replay_edges(outputs)[:limit]:
        rows.append(
            {
                "chain_id": stable_row_id("P47CH", edge.get("edge_id"), edge.get("from_node_id"), edge.get("to_node_id")),
                "edge_id": edge.get("edge_id"),
                "from_node_id": edge.get("from_node_id"),
                "to_node_id": edge.get("to_node_id"),
                "continuity_status": "provable" if edge.get("from_node_id") and edge.get("to_node_id") else "review",
                "proof_basis": "static_graph_edge",
                "human_review_required": True,
            }
        )
    if not rows:
        for sequence in replay_sequences(outputs, 12):
            rows.append(
                {
                    "chain_id": stable_row_id("P47CH", sequence.get("sequence_id")),
                    "edge_id": None,
                    "from_node_id": sequence.get("previous_event_id"),
                    "to_node_id": sequence.get("source_event_id"),
                    "continuity_status": "provable" if sequence.get("source_event_id") else "review",
                    "proof_basis": "static_replay_sequence",
                    "human_review_required": True,
                }
            )
    return rows


def render_replay_table(rows: list[dict], fields: list[str], id_field: str) -> str:
    header = "".join(f"<th scope='col'>{e(field.replace('_', ' ').title())}</th>" for field in fields)
    body = []
    for row in rows:
        cells = "".join(f"<td>{e(row.get(field))}</td>" for field in fields)
        body.append(f"<tr id='{e(row.get(id_field) or stable_row_id('P47ROW', row))}' tabindex='-1'>{cells}</tr>")
    return f"<section class='panel'><table class='data-table'><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></section>"


def render_replay_page(
    title: str,
    filename: str,
    rows: list[dict],
    fields: list[str],
    id_field: str,
    metrics: list[tuple[str, object]],
    extra: str = "",
) -> dict[str, str]:
    proof_panel = (
        "<section class='panel' aria-labelledby='replay-proof'><h2 id='replay-proof'>Deterministic Replay Proof</h2>"
        "<p class='muted'>Replay checks are computed from static registries, relative routes, declared breadcrumbs, and append-only continuity edges without browser automation.</p></section>"
    )
    body = f"<section class='panel'><p>{e(PHASE47_LIMITATION)}</p></section>{proof_panel}{extra}"
    body += compact_metrics(metrics)
    body += render_replay_table(rows, fields, id_field)
    return {filename: simple_review_page(title, "Operational Replay", filename, body, REPLAY_PAGE_LINKS)}


def score_from_counts(covered: int, total: int) -> float:
    return bounded_score(float(covered), float(total))
