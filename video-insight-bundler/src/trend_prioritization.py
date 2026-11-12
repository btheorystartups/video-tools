"""Trend prioritization for longitudinal export review."""

from __future__ import annotations

from stability import deterministic_id, utc_now_iso


def build_trend_priority_registry(change_report: dict) -> dict:
    trends = []
    for change in change_report.get("meaningful_changes", [])[:20]:
        score = int(change.get("change_priority_score") or 50)
        trends.append(
            {
                "trend_priority_id": deterministic_id("TPRI", change.get("artifact"), change.get("change_type")),
                "artifact": change.get("artifact"),
                "trend_type": change.get("change_type"),
                "priority_score": score,
                "review_focus": change.get("summary"),
            }
        )
    trends.sort(key=lambda row: row["priority_score"], reverse=True)
    return {"analysis_status": "complete", "method": "trend_prioritization_v77", "generated_at_utc": utc_now_iso(), "trend_priorities": trends, "summary": {"trend_priority_count": len(trends)}}
