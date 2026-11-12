"""Reviewer checklist generation."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


WORKFLOWS = ["executive", "governance", "recommendation", "audit", "evidence", "continuity", "delta"]


def build_review_checklists(priorities: dict, sessions: dict | None = None) -> dict:
    rows = []
    top_actions = priorities.get("priorities", [])[:5]
    for workflow in WORKFLOWS:
        rows.append(
            {
                "checklist_id": deterministic_id("RCHK", workflow, [item.get("priority_id") for item in top_actions]),
                "workflow": workflow,
                "review_complete_checklist": [
                    {"item": "Top findings reviewed", "completed": False},
                    {"item": "Evidence gaps recorded", "completed": False},
                    {"item": "Unresolved questions captured", "completed": False},
                    {"item": "Recommended next action selected", "completed": False},
                    {"item": "Handoff summary prepared", "completed": False},
                ],
                "unresolved_questions": [question for item in top_actions[:3] for question in item.get("review_questions", [])[:1]],
                "follow_up_recommendations": [item.get("recommended_action") for item in top_actions[:3]],
                "recommended_stopping_points": ["After top three priority actions", "After all high-severity findings"],
            }
        )
    return {"analysis_status": "complete", "method": "review_checklist_engine_v76", "generated_at_utc": utc_now_iso(), "checklists": rows, "summary": {"workflow_count": len(rows)}}
