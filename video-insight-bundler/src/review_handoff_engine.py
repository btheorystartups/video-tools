"""Static handoff summary generation."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def build_review_handoff_registry(synthesis: dict, checklists: dict) -> dict:
    handoffs = []
    for checklist in checklists.get("checklists") or []:
        handoffs.append(
            {
                "handoff_id": deterministic_id("RHAND", checklist.get("workflow")),
                "workflow": checklist.get("workflow"),
                "summary_template": "Decision:\nEvidence checked:\nOpen risks:\nRecommended next action:\nOwner:\n",
                "top_findings_to_reference": [row.get("finding_id") for row in synthesis.get("top_findings", [])[:3]],
                "evidence_gaps": ["Record any missing, stale, or contradictory evidence found during review."],
                "recommended_next_actions": [row for row in checklist.get("follow_up_recommendations", []) if row],
            }
        )
    return {"analysis_status": "complete", "method": "review_handoff_engine_v76", "generated_at_utc": utc_now_iso(), "handoffs": handoffs, "summary": {"handoff_count": len(handoffs)}}
