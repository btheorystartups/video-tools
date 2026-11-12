"""Static HTML packet exporter for review continuity."""

from __future__ import annotations

from dashboard_layout import e
from review_operational_common import REVIEW_LIMITATION, card_grid, compact_metrics, simple_review_page
from stability import deterministic_id
from review_operational_common import review_artifact


def build_review_packet_export_registry(packets: dict) -> dict:
    packet_rows = packets.get("packets") or []
    exports = []
    for row in packet_rows:
        exports.append({"export_id": deterministic_id("RPEXP", row.get("packet_id")), "packet_id": row.get("packet_id"), "packet_type": row.get("packet_type"), "html_page": row.get("html_page"), "pdf_runtime_required": False, "static_local_only": True})
    output = review_artifact("deterministic_review_packet_export_registry_v1")
    output.update({"review_packet_export_registry_id": deterministic_id("RPEXPREG", [row["export_id"] for row in exports]), "exports": exports, "summary": {"export_count": len(exports), "pdf_runtime_required": False}})
    return output


def review_nav_links() -> list[tuple[str, str]]:
    return [
        ("Dashboard", "../dashboard.html"),
        ("Workstation", "../workstation/workstation_index.html"),
        ("Review Session", "review_session_dashboard.html"),
        ("Annotations", "reviewer_annotations.html"),
        ("Progress", "review_progress_dashboard.html"),
        ("Resume", "review_resume_dashboard.html"),
        ("Follow-up", "review_followup_dashboard.html"),
        ("Queues", "review_queue_dashboard.html"),
        ("Escalations", "escalation_dashboard.html"),
        ("Activity", "review_activity_history.html"),
        ("Packets", "printable_review_packet_index.html"),
        ("Rationale", "reviewer_rationale_dashboard.html"),
    ]


def render_review_dashboards(outputs: dict) -> dict[str, str]:
    links = review_nav_links()
    session = outputs.get("review_session_registry") or {}
    progress = outputs.get("review_progress_summary") or {}
    annotations = outputs.get("reviewer_annotations") or {}
    checkpoints = outputs.get("review_checkpoints") or {}
    resume = outputs.get("review_resume_index") or {}
    followups = outputs.get("review_followup_registry") or {}
    queues = outputs.get("review_queue_registry") or {}
    escalations = outputs.get("review_escalation_registry") or {}
    activity = outputs.get("review_activity_history") or {}
    rationale = outputs.get("reviewer_rationale_registry") or {}
    packets = outputs.get("printable_review_packets") or {}
    pages = {}
    pages["review_session_dashboard.html"] = simple_review_page("Review Session Dashboard", "Operational Continuity", "review_session_dashboard.html", compact_metrics([("Sessions", (session.get("summary") or {}).get("session_count", 0)), ("Pending follow-ups", (session.get("summary") or {}).get("pending_followup_count", 0)), ("Escalations", (session.get("summary") or {}).get("active_escalation_count", 0))]) + card_grid(session.get("sessions") or [], ["last_reviewed_segment", "last_opened_timeline", "last_review_journey", "review_completion_state"], "session_id") + card_grid(checkpoints.get("checkpoints") or [], ["current_page", "current_segment", "next_recommended_action"], "checkpoint_name"), links)
    pages["reviewer_annotations.html"] = simple_review_page("Reviewer Annotations", "Annotation Workflow", "reviewer_annotations.html", compact_metrics([("Annotations", (annotations.get("summary") or {}).get("annotation_count", 0)), ("Follow-ups", (annotations.get("summary") or {}).get("followup_required_count", 0)), ("Escalations", (annotations.get("summary") or {}).get("escalation_required_count", 0))]) + card_grid(annotations.get("annotations") or [], ["annotation_type", "severity", "review_status", "followup_required", "escalation_required", "annotation_text"], "annotation_id"), links)
    pages["review_progress_dashboard.html"] = simple_review_page("Review Progress Dashboard", "Completion Tracking", "review_progress_dashboard.html", compact_metrics([("Total items", progress.get("total_review_item_count", 0)), ("Reviewed", progress.get("reviewed_item_count", 0)), ("Open follow-ups", progress.get("open_followup_count", 0)), ("Open escalations", progress.get("open_escalation_count", 0))]), links)
    pages["review_resume_dashboard.html"] = simple_review_page("Review Resume Dashboard", "Session Resume", "review_resume_dashboard.html", card_grid(resume.get("resume_links") or [], ["label", "href", "reason"], "label"), links)
    pages["review_followup_dashboard.html"] = simple_review_page("Review Follow-up Dashboard", "Follow-up Tracking", "review_followup_dashboard.html", card_grid(followups.get("followup_items") or [], ["followup_type", "severity", "status", "required_action"], "followup_id"), links)
    pages["review_queue_dashboard.html"] = simple_review_page("Review Queue Dashboard", "Operational Queues", "review_queue_dashboard.html", compact_metrics([("Queue items", (queues.get("summary") or {}).get("queue_item_count", 0)), ("Escalation queue", (queues.get("summary") or {}).get("escalation_required_count", 0))]) + card_grid(queues.get("queue_items") or [], ["queue_type", "severity", "effort_estimate", "expected_review_time", "review_priority_score", "suggested_next_action"], "queue_id"), links)
    pages["escalation_dashboard.html"] = simple_review_page("Escalation Dashboard", "Escalation Workflow", "escalation_dashboard.html", card_grid(escalations.get("escalation_items") or [], ["escalation_type", "severity", "escalation_reason", "suggested_reviewer_action"], "escalation_id"), links)
    pages["review_activity_history.html"] = simple_review_page("Review Activity History", "Audit History", "review_activity_history.html", card_grid(activity.get("activities") or [], ["activity_type", "related_item", "source_artifact", "audit_note"], "activity_id"), links)
    pages["printable_review_packet_index.html"] = simple_review_page("Printable Review Packet Index", "Review Packets", "printable_review_packet_index.html", card_grid(packets.get("packets") or [], ["packet_type", "summary", "html_page"], "packet_id"), links)
    pages["reviewer_rationale_dashboard.html"] = simple_review_page("Reviewer Rationale Dashboard", "Rationale Capture", "reviewer_rationale_dashboard.html", card_grid(rationale.get("rationales") or [], ["rationale_type", "related_item", "governance_impact", "followup_required", "escalation_required"], "rationale_id"), links)
    return pages


def render_packet_page(packet: dict) -> str:
    rows = "".join(
        f"<section class='panel'><h2>{e(label)}</h2><p>{e(value)}</p></section>"
        for label, value in [
            ("Summary", packet.get("summary")),
            ("Current Review State", packet.get("current_review_state")),
            ("Unresolved Items", packet.get("unresolved_items")),
            ("Key Recommendations", packet.get("key_recommendations")),
            ("Evidence References", packet.get("evidence_references")),
            ("Reviewer Annotations", packet.get("reviewer_annotations")),
            ("Rationale", packet.get("rationale")),
            ("Escalation Items", packet.get("escalation_items")),
            ("Next Best Actions", packet.get("next_best_actions")),
            ("Timeline Snapshots", packet.get("timeline_snapshots")),
            ("Limitations", REVIEW_LIMITATION),
        ]
    )
    links = [("Packet Index", "../printable_review_packet_index.html"), ("Review Dashboard", "../review_session_dashboard.html")]
    return simple_review_page(packet.get("packet_type") or "Review Packet", "Printable Packet", "", rows, links, depth=3)
