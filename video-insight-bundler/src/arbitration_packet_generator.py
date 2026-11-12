"""Static arbitration packet generation for adjudication conflicts."""

from __future__ import annotations

from dashboard_layout import e
from reviewer_adjudication import ADJUDICATION_LIMITATION, adjudication_artifact
from review_operational_common import card_grid, compact_metrics, simple_review_page
from stability import deterministic_id


def build_arbitration_packet_registry(conflict_resolution_registry: dict, reviewer_adjudication_registry: dict, rationale_diff_registry: dict, governance_conflict_analysis: dict, unresolved_ambiguity_registry: dict, adjudication_queue_registry: dict) -> dict:
    adjudications = {row.get("conflict_id"): row for row in reviewer_adjudication_registry.get("adjudications") or []}
    diffs = {row.get("conflict_id"): row for row in rationale_diff_registry.get("rationale_diffs") or []}
    impacts = {row.get("conflict_id"): row for row in governance_conflict_analysis.get("governance_conflicts") or []}
    ambiguities = {row.get("conflict_id"): row for row in unresolved_ambiguity_registry.get("ambiguities") or []}
    queue = {row.get("conflict_id"): row for row in adjudication_queue_registry.get("queue_items") or []}
    packets = []
    for workflow in conflict_resolution_registry.get("conflict_resolution_workflows") or []:
        conflict_id = workflow.get("conflict_id")
        packet_id = deterministic_id("APKT", conflict_id, workflow.get("resolution_state"))
        packet_type = _packet_type(impacts.get(conflict_id) or {}, ambiguities.get(conflict_id) or {})
        packets.append(
            {
                "packet_id": packet_id,
                "conflict_id": conflict_id,
                "packet_type": packet_type,
                "html_page": f"packets/{_packet_prefix(packet_type)}_{packet_id.lower()}.html",
                "conflict_summary": workflow,
                "reviewer_adjudication": adjudications.get(conflict_id) or {},
                "rationale_comparison": diffs.get(conflict_id) or {},
                "evidence_comparison": {
                    "agreement": (diffs.get(conflict_id) or {}).get("evidence_agreement") or [],
                    "disagreement": (diffs.get(conflict_id) or {}).get("evidence_disagreement") or [],
                },
                "governance_impact": impacts.get(conflict_id) or {},
                "unresolved_questions": (ambiguities.get(conflict_id) or {}).get("ambiguity_types") or workflow.get("unresolved_questions") or [],
                "escalation_state": workflow.get("resolution_state"),
                "queue_priority": queue.get(conflict_id) or {},
                "suggested_manual_review_path": workflow.get("required_manual_actions") or [],
            }
        )
    artifact = adjudication_artifact("deterministic_arbitration_packet_registry_v1")
    artifact.update({"arbitration_packet_registry_id": deterministic_id("APKTREG", [row["packet_id"] for row in packets]), "packets": packets, "summary": {"packet_count": len(packets), "governance_arbitration_packet_count": sum(1 for row in packets if row["packet_type"] == "governance_arbitration_packet")}})
    return artifact


def render_arbitration_dashboards(outputs: dict) -> dict[str, str]:
    links = _links()
    return {
        "conflict_resolution_dashboard.html": simple_review_page("Conflict Resolution Dashboard", "Adjudication", "conflict_resolution_dashboard.html", _limitation() + card_grid((outputs.get("conflict_resolution_registry") or {}).get("conflict_resolution_workflows") or [], ["conflict_type", "resolution_state", "reviewer_role_context", "required_manual_actions"], "workflow_id"), links),
        "reviewer_disagreement_dashboard.html": simple_review_page("Reviewer Disagreement Dashboard", "Adjudication", "reviewer_disagreement_dashboard.html", _limitation() + card_grid((outputs.get("reviewer_disagreement_registry") or {}).get("disagreements") or [], ["source_item_id", "reviewer_a_state", "reviewer_b_state", "governance_implications", "suggested_manual_review"], "disagreement_id"), links),
        "rationale_diff_dashboard.html": simple_review_page("Rationale Diff Dashboard", "Adjudication", "rationale_diff_dashboard.html", _limitation() + card_grid((outputs.get("rationale_diff_registry") or {}).get("rationale_diffs") or [], ["rationale_overlaps", "rationale_conflicts", "evidence_agreement", "evidence_disagreement", "unresolved_ambiguity"], "rationale_diff_id"), links),
        "governance_conflict_dashboard.html": simple_review_page("Governance Conflict Dashboard", "Adjudication", "governance_conflict_dashboard.html", _limitation() + card_grid((outputs.get("governance_conflict_analysis") or {}).get("governance_conflicts") or [], ["governance_conflict_categories", "governance_severity", "governance_impact_summary", "requires_arbitration"], "governance_conflict_id"), links),
        "unresolved_ambiguity_dashboard.html": simple_review_page("Unresolved Ambiguity Dashboard", "Adjudication", "unresolved_ambiguity_dashboard.html", _limitation() + card_grid((outputs.get("unresolved_ambiguity_registry") or {}).get("ambiguities") or [], ["ambiguity_types", "ambiguity_status", "governance_sensitive", "suggested_manual_question"], "ambiguity_id"), links),
        "adjudication_queue_dashboard.html": simple_review_page("Adjudication Queue Dashboard", "Adjudication", "adjudication_queue_dashboard.html", _limitation() + card_grid((outputs.get("adjudication_queue_registry") or {}).get("queue_items") or [], ["queue_types", "priority_score", "governance_severity", "suggested_next_action"], "queue_item_id"), links),
        "arbitration_packet_dashboard.html": simple_review_page("Arbitration Packet Dashboard", "Adjudication", "arbitration_packet_dashboard.html", _limitation() + card_grid((outputs.get("arbitration_packet_registry") or {}).get("packets") or [], ["packet_type", "conflict_id", "escalation_state", "html_page"], "packet_id"), links),
        "consensus_workflow_dashboard.html": simple_review_page("Consensus Workflow Dashboard", "Adjudication", "consensus_workflow_dashboard.html", _limitation() + card_grid((outputs.get("consensus_workflow_registry") or {}).get("consensus_workflows") or [], ["consensus_state", "required_participants", "rationale_conflicts", "manual_consensus_required"], "consensus_workflow_id"), links),
        "conflict_heatmap_dashboard.html": simple_review_page("Conflict Heatmap Dashboard", "Adjudication", "conflict_heatmap_dashboard.html", _limitation() + card_grid((outputs.get("conflict_heatmap") or {}).get("heatmap_cells") or [], ["governance_severity", "unresolved_ambiguity", "reviewer_disagreement_count", "escalation_density", "unresolved_followups"], "heatmap_cell_id"), links),
    }


def render_arbitration_packet_page(packet: dict) -> str:
    metrics = compact_metrics([("Conflict", packet.get("conflict_id")), ("Type", packet.get("packet_type")), ("Escalation", packet.get("escalation_state"))])
    sections = [
        ("Conflict Summary", packet.get("conflict_summary")),
        ("Rationale Comparison", packet.get("rationale_comparison")),
        ("Evidence Comparison", packet.get("evidence_comparison")),
        ("Governance Impact", packet.get("governance_impact")),
        ("Unresolved Questions", packet.get("unresolved_questions")),
        ("Suggested Manual Review Path", packet.get("suggested_manual_review_path")),
    ]
    body = _limitation() + metrics + "".join(f"<section class='panel'><h2>{e(title)}</h2><pre>{e(value)}</pre></section>" for title, value in sections)
    return simple_review_page(f"Arbitration Packet {packet.get('packet_id')}", "Adjudication Packet", "../arbitration_packet_dashboard.html", body, _packet_links(), depth=3)


def _packet_type(impact: dict, ambiguity: dict) -> str:
    if impact.get("requires_arbitration"):
        return "governance_arbitration_packet"
    if ambiguity.get("ambiguity_types"):
        return "unresolved_ambiguity_packet"
    return "reviewer_conflict_packet"


def _packet_prefix(packet_type: str) -> str:
    return {"governance_arbitration_packet": "governance_arbitration_packet", "unresolved_ambiguity_packet": "unresolved_ambiguity_packet"}.get(packet_type, "reviewer_conflict_packet")


def _limitation() -> str:
    return f"<section class='panel'><p>{e(ADJUDICATION_LIMITATION)}</p></section>"


def _links() -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Reconciliation", "../reconciliation/reconciliation_dashboard.html"),
        ("Resolution", "conflict_resolution_dashboard.html"),
        ("Disagreements", "reviewer_disagreement_dashboard.html"),
        ("Rationale", "rationale_diff_dashboard.html"),
        ("Governance", "governance_conflict_dashboard.html"),
        ("Ambiguity", "unresolved_ambiguity_dashboard.html"),
        ("Queues", "adjudication_queue_dashboard.html"),
        ("Packets", "arbitration_packet_dashboard.html"),
        ("Consensus", "consensus_workflow_dashboard.html"),
        ("Heatmap", "conflict_heatmap_dashboard.html"),
    ]


def _packet_links() -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../../dashboard.html"),
        ("Reconciliation", "../../reconciliation/reconciliation_dashboard.html"),
        ("Resolution", "../conflict_resolution_dashboard.html"),
        ("Disagreements", "../reviewer_disagreement_dashboard.html"),
        ("Rationale", "../rationale_diff_dashboard.html"),
        ("Governance", "../governance_conflict_dashboard.html"),
        ("Ambiguity", "../unresolved_ambiguity_dashboard.html"),
        ("Queues", "../adjudication_queue_dashboard.html"),
        ("Packets", "../arbitration_packet_dashboard.html"),
        ("Consensus", "../consensus_workflow_dashboard.html"),
        ("Heatmap", "../conflict_heatmap_dashboard.html"),
    ]
