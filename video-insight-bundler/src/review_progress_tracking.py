"""Offline progress templates for static review packages."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def build_review_progress_templates(checklists: dict) -> dict:
    templates = []
    for checklist in checklists.get("checklists") or []:
        workflow = checklist.get("workflow")
        templates.append(
            {
                "progress_template_id": deterministic_id("RPROG", workflow),
                "workflow": workflow,
                "completion_estimate_minutes": 20 + len(checklist.get("review_complete_checklist") or []) * 5,
                "progress_fields": ["not_started", "in_progress", "blocked", "complete"],
                "note_fields": ["decision", "evidence_gap", "follow_up", "handoff_owner"],
                "recommended_next_actions": checklist.get("follow_up_recommendations") or [],
            }
        )
    return {"analysis_status": "complete", "method": "review_progress_tracking_v76", "generated_at_utc": utc_now_iso(), "templates": templates, "summary": {"template_count": len(templates)}}
