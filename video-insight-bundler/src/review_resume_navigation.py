"""Resume navigation for review continuity."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id


def build_review_resume_index(session_registry: dict, checkpoints: dict, queue_registry: dict, followups: dict, escalations: dict) -> dict:
    session = ((session_registry.get("sessions") or [{}])[0])
    checkpoint = ((checkpoints.get("checkpoints") or [{}])[0])
    queue = ((queue_registry.get("queue_items") or [{}])[0])
    links = [
        {"resume_id": deterministic_id("RES", "last", session.get("session_id")), "label": "Continue where you left off", "href": checkpoint.get("current_page") or "visualizations/review/review_session_dashboard.html", "reason": "Last explicit checkpoint."},
        {"resume_id": deterministic_id("RES", "blocker", len(session.get("pending_decisions") or [])), "label": "Continue unresolved blocker review", "href": "visualizations/review/review_queue_dashboard.html", "reason": "Open blockers or pending governance decisions."},
        {"resume_id": deterministic_id("RES", "pacing", queue.get("queue_id")), "label": "Continue pacing review", "href": "visualizations/review/review_queue_dashboard.html", "reason": "Pacing queue and timeline markers are available."},
        {"resume_id": deterministic_id("RES", "priority", queue.get("queue_id")), "label": "Continue highest-priority queue", "href": "visualizations/review/review_queue_dashboard.html", "reason": "Highest priority deterministic queue item."},
        {"resume_id": deterministic_id("RES", "escalation", len(escalations.get("escalation_items") or [])), "label": "Continue escalation workflow", "href": "visualizations/review/escalation_dashboard.html", "reason": "Escalation-required items are open."},
    ]
    output = review_artifact("deterministic_review_resume_index_v1")
    output.update({"review_resume_index_id": deterministic_id("RESREG", [row["resume_id"] for row in links]), "resume_links": links, "summary": {"resume_link_count": len(links), "open_followup_count": len(followups.get("followup_items") or []), "open_escalation_count": len(escalations.get("escalation_items") or [])}})
    return output
