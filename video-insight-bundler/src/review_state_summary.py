"""Operational review state summary for the workstation."""

from __future__ import annotations

from intelligence_common import base_artifact, num
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_review_state_summary(outputs: dict, shortcuts: dict, heatmaps: dict) -> dict:
    recs = (outputs.get("recommendation_traceability") or {}).get("traceability_entries") or []
    blockers = (outputs.get("tier_1_blocker_disposition") or {}).get("blocker_dispositions") or []
    valid = outputs.get("validated_human_decisions") or {}
    rejected = outputs.get("rejected_human_decisions") or {}
    gatekeeper = outputs.get("reassessment_gatekeeper") or {}
    high_regions = []
    for heatmap in heatmaps.get("heatmaps") or []:
        for cell in heatmap.get("cells") or []:
            if cell.get("severity") == "high":
                high_regions.append({"video_id": heatmap.get("video_id"), "segment_id": cell.get("segment_id"), "severity": "high", "time_region": cell.get("time_region")})
    low_effort = [rec for rec in recs if "low" in str(rec.get("effort_estimate")).lower()]
    output = base_artifact(method="deterministic_review_state_summary_v1")
    output.update(
        {
            "review_state_summary_id": deterministic_id("RSSUM", len(recs), len(blockers), gatekeeper.get("unresolved_blocker_count")),
            "total_recommendations": len(recs),
            "high_priority_recommendations": sum(1 for row in recs if row.get("severity") == "high" or num(row.get("priority_score")) >= 0.75),
            "tier_1_blockers": len(blockers),
            "unresolved_blockers": sum(1 for row in blockers if row.get("disposition") in {None, "proposed", "confirmed_blocker", "deferred"}) or gatekeeper.get("unresolved_blocker_count", 0),
            "valid_human_decisions": (valid.get("summary") or {}).get("valid_decision_count", 0),
            "rejected_human_decisions": (rejected.get("summary") or {}).get("rejected_decision_count", 0),
            "top_review_shortcuts": (shortcuts.get("shortcuts") or [])[:8],
            "most_severe_timeline_regions": high_regions[:10],
            "lowest_effort_highest_impact_actions": [{"recommendation_id": row.get("recommendation_id"), "title": row.get("title"), "priority_score": row.get("priority_score")} for row in low_effort[:10]],
            "readiness_cap_status": {"readiness_can_change": gatekeeper.get("readiness_can_change"), "unresolved_blocker_count": gatekeeper.get("unresolved_blocker_count")},
            "next_recommended_review_journey": "governance_blocker_review" if blockers else "quick_executive_review",
            "summary": {"recommendation_count": len(recs), "unresolved_blocker_count": gatekeeper.get("unresolved_blocker_count", 0)},
            "limitations": [LIMITATION],
        }
    )
    return output
