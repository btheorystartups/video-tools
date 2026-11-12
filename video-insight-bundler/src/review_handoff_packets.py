"""Review handoff, governance, escalation, and printable packet builders."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id


PACKET_TYPES = [
    "executive_review_packet",
    "governance_review_packet",
    "escalation_packet",
    "blocker_review_packet",
    "pacing_optimization_packet",
    "rhetorical_optimization_packet",
    "unresolved_followup_packet",
]


def _packet(packet_type: str, state: dict, annotations: dict, rationales: dict, followups: dict, escalations: dict, queues: dict) -> dict:
    packet_id = deterministic_id("RPKT", packet_type, (state.get("summary") or {}).get("state_item_count"), (followups.get("summary") or {}).get("followup_count"))
    return {
        "packet_id": packet_id,
        "packet_type": packet_type,
        "summary": f"{packet_type.replace('_', ' ').title()} for deterministic local review continuity.",
        "current_review_state": state.get("summary") or {},
        "unresolved_items": [row.get("item_id") for row in state.get("state_items") or [] if row.get("review_state") in {"followup_required", "escalation_required", "in_review"}][:30],
        "key_recommendations": [row.get("related_artifact") for row in queues.get("queue_items") or [] if row.get("related_recommendations")][:20],
        "evidence_references": ["timeline/temporal_evidence_index.json", "recommendations/recommendation_traceability.json", "governance/governance_diagnostics.json"],
        "reviewer_annotations": [row.get("annotation_id") for row in annotations.get("annotations") or []][:30],
        "rationale": [row.get("rationale_id") for row in rationales.get("rationales") or []][:30],
        "escalation_items": [row.get("escalation_id") for row in escalations.get("escalation_items") or []][:30],
        "next_best_actions": [row.get("suggested_next_action") for row in queues.get("queue_items") or []][:10],
        "timeline_snapshots": ["visualizations/timeline/enhanced_corpus_timeline_overview.html"],
        "html_page": f"visualizations/review/packets/{packet_type}_{packet_id.lower()}.html",
    }


def build_review_handoff_packets(state: dict, annotations: dict, rationales: dict, followups: dict, escalations: dict, queues: dict) -> dict:
    packets = [_packet(kind, state, annotations, rationales, followups, escalations, queues) for kind in PACKET_TYPES]
    handoff = review_artifact("deterministic_review_handoff_packets_v1")
    handoff.update({"review_handoff_packets_id": deterministic_id("RHAND", [row["packet_id"] for row in packets]), "packets": packets, "summary": {"packet_count": len(packets)}})
    governance = review_artifact("deterministic_governance_review_packets_v1")
    governance_packets = [row for row in packets if "governance" in row["packet_type"] or "blocker" in row["packet_type"]]
    governance.update({"governance_review_packets_id": deterministic_id("RGOVP", [row["packet_id"] for row in governance_packets]), "packets": governance_packets, "summary": {"packet_count": len(governance_packets)}})
    escalation = review_artifact("deterministic_escalation_packets_v1")
    escalation_packets = [row for row in packets if "escalation" in row["packet_type"]]
    escalation.update({"escalation_packets_id": deterministic_id("RESCP", [row["packet_id"] for row in escalation_packets]), "packets": escalation_packets, "summary": {"packet_count": len(escalation_packets)}})
    printable = review_artifact("deterministic_printable_review_packets_v1")
    printable.update({"printable_review_packets_id": deterministic_id("RPRNP", [row["packet_id"] for row in packets]), "packets": packets, "summary": {"packet_count": len(packets)}})
    return {"review_handoff_packets": handoff, "governance_review_packets": governance, "escalation_packets": escalation, "printable_review_packets": printable}
