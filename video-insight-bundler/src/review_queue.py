"""Static editorial review queue generation."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


def _add(items: list[dict], source: str, priority: float, reason: str, artifact: str, refs: list[str], action: str) -> None:
    items.append(
        {
            "review_item_id": deterministic_id("REVQ", source, reason, artifact, refs),
            "priority_score": clamp(priority),
            "reason": reason,
            "source_video": source,
            "artifact_path": artifact,
            "evidence_references": refs,
            "suggested_human_action": action,
            "non_mutating_status": "review_only_no_media_or_timeline_mutation",
        }
    )


def build_review_queue(analyses: list[dict]) -> dict:
    items = []
    segment_index = []
    recommendation_index = []
    pressure_index = []
    for analysis in analyses:
        manifest = analysis.get("manifest") or {}
        source = manifest.get("source_video") or analysis.get("analysis_dir")
        readiness = analysis.get("release_readiness") or {}
        score = readiness.get("release_readiness_score") or 0.0
        if score < 0.68:
            _add(items, source, 1.0 - score, f"Readiness class is {readiness.get('release_readiness_class')}.", "revision_graph/release_readiness_report.json", ["revision_graph/release_readiness_report.json"], "Review blocking issues and weakest evidence.")
        pressure_rows = ((analysis.get("editorial_pressure") or {}).get("summary") or {}).get("chronic_pressure_regions") or []
        for row in pressure_rows:
            priority = row.get("cumulative_pressure_score") or row.get("pressure_score") or 0.0
            refs = [f"sequence/editorial_pressure.json#{row.get('segment_id')}"]
            _add(items, source, priority, "Chronic editorial pressure region.", "sequence/editorial_pressure.json", refs, "Inspect segment pressure components and determine whether a bridge, callback resolution, or pacing review is needed.")
            pressure_index.append({"source_video": source, "segment_id": row.get("segment_id"), "priority_score": priority, "artifact_path": "sequence/editorial_pressure.json"})
        for rec in (analysis.get("recommendations") or {}).get("recommendations", [])[:60]:
            priority = (rec.get("confidence") or 0.0) * {"high": 1.0, "medium": 0.72, "low": 0.45}.get(rec.get("severity"), 0.5)
            refs = rec.get("affected_segment_ids") or []
            _add(items, source, priority, f"Recommendation requires review: {rec.get('issue_type')}.", "recommendations.json", refs, rec.get("suggested_edit") or "Review recommendation evidence.")
            recommendation_index.append({"source_video": source, "issue_type": rec.get("issue_type"), "priority_score": clamp(priority), "artifact_path": "recommendations.json", "segment_ids": refs})
            for segment_id in refs:
                segment_index.append({"source_video": source, "segment_id": segment_id, "artifact_path": "scene_segments.json", "reason": rec.get("issue_type")})
        counter = analysis.get("counterfactual_simulation") or {}
        for row in counter.get("counterfactual_scenarios", []):
            uncertainty = row.get("counterfactual_uncertainty") or 0.0
            impact = (row.get("estimated_shifts") or {}).get("readiness_shift") or 0.0
            if uncertainty >= 0.6 or (impact >= 0.02 and uncertainty >= 0.45):
                _add(items, source, uncertainty, f"High-uncertainty counterfactual: {row.get('scenario')}.", "sequence/counterfactual_simulation.json", [row.get("counterfactual_id")], "Review scenario assumptions before using it to prioritize edits.")
    items = sorted(items, key=lambda row: (-row["priority_score"], row["source_video"] or "", row["review_item_id"]))
    output = base_artifact(method="deterministic_editorial_review_queue_v1")
    output.update(
        {
            "review_queue_id": deterministic_id("QUEUE", [row.get("review_item_id") for row in items]),
            "review_items": items,
            "summary": {
                "review_item_count": len(items),
                "high_priority_count": sum(1 for row in items if row["priority_score"] >= 0.72),
                "video_count": len(analyses),
            },
            "indexes": {
                "segment_review_index": segment_index,
                "recommendation_review_index": recommendation_index,
                "pressure_review_index": pressure_index,
            },
        }
    )
    return output
