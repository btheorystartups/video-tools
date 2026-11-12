"""Timeline markers derived from reviewer annotations."""

from __future__ import annotations

from review_operational_common import review_artifact
from stability import deterministic_id


def _marker_type(annotation_type: str) -> str:
    return {
        "blocker_annotation": "blocker note",
        "followup_note": "follow-up marker",
        "escalation_note": "escalation marker",
        "optimization_rationale": "optimization marker",
        "accepted_risk_rationale": "accepted-risk marker",
        "governance_annotation": "governance marker",
    }.get(annotation_type, "reviewer note")


def build_annotation_timeline_markers(annotations: dict, temporal_index: dict, review_queue_registry: dict | None = None, checkpoints: dict | None = None) -> dict:
    entries = {(row.get("video_id"), row.get("segment_id")): row for row in (temporal_index.get("temporal_evidence_entries") or [])}
    queue_items = (review_queue_registry or {}).get("queue_items") or []
    queues_by_segment = {}
    for item in queue_items:
        for segment in item.get("related_segments") or []:
            queues_by_segment.setdefault(segment, []).append(item.get("queue_id"))
    checkpoint_id = ((checkpoints or {}).get("checkpoints") or [{}])[0].get("checkpoint_id")
    markers = []
    for row in annotations.get("annotations") or []:
        if not row.get("related_segment"):
            continue
        entry = entries.get((row.get("related_video"), row.get("related_segment"))) or {}
        marker_id = deterministic_id("AMRK", row.get("annotation_id"), row.get("related_segment"))
        markers.append(
            {
                "marker_id": marker_id,
                "marker_type": _marker_type(row.get("annotation_type")),
                "annotation_id": row.get("annotation_id"),
                "video_id": row.get("related_video"),
                "segment_id": row.get("related_segment"),
                "time_region": {"start_sec": entry.get("timestamp_start"), "end_sec": entry.get("timestamp_end")},
                "evidence_refs": row.get("evidence_refs") or [],
                "related_recommendation": row.get("related_recommendation"),
                "related_review_queue": queues_by_segment.get(row.get("related_segment"), []),
                "related_checkpoint": checkpoint_id,
                "timeline_anchor": f"segment-{row.get('related_segment')}",
                "html_target": f"visualizations/timeline/enhanced_video_timeline_{row.get('related_video')}.html#segment-{row.get('related_segment')}",
            }
        )
    output = review_artifact("deterministic_annotation_timeline_markers_v1")
    output.update({"annotation_timeline_markers_id": deterministic_id("AMREG", [row["marker_id"] for row in markers]), "markers": markers, "summary": {"marker_count": len(markers)}})
    return output
