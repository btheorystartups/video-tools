"""Crosslink index for Phase 34 workstation artifacts."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_workstation_crosslink_index(outputs: dict) -> dict:
    links = []
    trace = (outputs.get("recommendation_traceability") or {}).get("traceability_entries") or []
    overlays = (outputs.get("timeline_overlay_registry") or {}).get("overlays") or []
    entries = (outputs.get("temporal_evidence_index") or {}).get("temporal_evidence_entries") or []
    for rec in trace:
        for segment in rec.get("affected_segments") or []:
            base = {"source_id": rec.get("recommendation_id"), "video_id": segment.get("video_id"), "segment_id": segment.get("segment_id"), "evidence_refs": rec.get("evidence_refs") or []}
            for link_type, target in [
                ("recommendation_to_timeline_region", f"visualizations/timeline/enhanced_video_timeline_{segment.get('video_id')}.html#segment-{segment.get('segment_id')}"),
                ("recommendation_to_segment_context", f"visualizations/timeline/segment_context_{segment.get('video_id')}_{segment.get('segment_id')}.html"),
                ("recommendation_to_evidence", "visualizations/recommendation_evidence_map.html"),
                ("recommendation_to_lineage", "visualizations/recommendation_lineage.html"),
                ("recommendation_to_optimization_path", "visualizations/optimization_effort_dashboard.html"),
            ]:
                links.append({"crosslink_id": deterministic_id("WCROSS", link_type, rec.get("recommendation_id"), segment.get("segment_id")), "crosslink_type": link_type, "target_path": target, **base})
    for entry in entries:
        for link_type, target in [
            ("segment_to_timeline", f"visualizations/timeline/enhanced_video_timeline_{entry.get('video_id')}.html#segment-{entry.get('segment_id')}"),
            ("segment_to_recommendations", "visualizations/recommendation_traceability.html"),
            ("segment_to_metric_spikes", "visualizations/timeline_metric_spikes.html"),
            ("segment_to_evidence", "visualizations/temporal_evidence_index.html"),
        ]:
            links.append({"crosslink_id": deterministic_id("WCROSS", link_type, entry.get("video_id"), entry.get("segment_id")), "crosslink_type": link_type, "source_id": entry.get("segment_id"), "video_id": entry.get("video_id"), "segment_id": entry.get("segment_id"), "target_path": target, "evidence_refs": entry.get("evidence_refs") or []})
    for overlay in overlays:
        links.append({"crosslink_id": deterministic_id("WCROSS", "overlay_to_evidence", overlay.get("overlay_id")), "crosslink_type": "overlay_to_evidence", "source_id": overlay.get("overlay_id"), "video_id": overlay.get("video_id"), "segment_id": overlay.get("segment_id"), "target_path": "visualizations/temporal_evidence_index.html", "evidence_refs": overlay.get("evidence_refs") or []})
        links.append({"crosslink_id": deterministic_id("WCROSS", "overlay_to_recommendations", overlay.get("overlay_id")), "crosslink_type": "overlay_to_recommendations", "source_id": overlay.get("overlay_id"), "video_id": overlay.get("video_id"), "segment_id": overlay.get("segment_id"), "target_path": "visualizations/recommendation_traceability.html", "evidence_refs": overlay.get("evidence_refs") or []})
    for link_type, target in [
        ("blocker_to_decision_intake", "visualizations/human_decision_intake.html"),
        ("blocker_to_governance_diagnostics", "visualizations/governance_diagnostics.html"),
        ("compare_to_source_videos", "visualizations/workstation/compare_readability_index.html"),
        ("review_journey_to_workstation_pages", "visualizations/workstation/workstation_index.html"),
    ]:
        links.append({"crosslink_id": deterministic_id("WCROSS", link_type), "crosslink_type": link_type, "source_id": link_type, "target_path": target, "evidence_refs": []})
    output = base_artifact(method="deterministic_workstation_crosslinks_v1")
    output.update({"workstation_crosslink_index_id": deterministic_id("WCROSSREG", [row["crosslink_id"] for row in links]), "crosslinks": links, "summary": {"crosslink_count": len(links)}, "limitations": [LIMITATION]})
    return output
