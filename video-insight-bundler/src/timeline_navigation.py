"""Timeline navigation manifest for static review pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_timeline_navigation_manifest(outputs: dict) -> dict:
    pages = [
        ("timeline_review_index", "visualizations/timeline_review_index.html"),
        ("corpus_timeline_overview", "visualizations/timeline/corpus_timeline_overview.html"),
        ("recommendation_traceability", "visualizations/recommendation_traceability.html"),
        ("recommendation_lineage", "visualizations/recommendation_lineage.html"),
        ("temporal_evidence_index", "visualizations/temporal_evidence_index.html"),
        ("profile_benchmark_packs", "visualizations/profile_benchmark_packs.html"),
        ("review_journey_index", "visualizations/review_journey_index.html"),
    ]
    anchors = []
    for entry in (outputs.get("temporal_evidence_index") or {}).get("temporal_evidence_entries") or []:
        anchors.append({"anchor_id": deterministic_id("TANCH", entry.get("video_id"), entry.get("segment_id")), "video_id": entry.get("video_id"), "segment_id": entry.get("segment_id"), "href": f"visualizations/timeline/segment_context_{entry.get('video_id')}_{entry.get('segment_id')}.html"})
    output = base_artifact(method="deterministic_timeline_navigation_manifest_v1")
    output.update({"timeline_navigation_manifest_id": deterministic_id("TNAV", pages, anchors), "persistent_links": [{"label": label, "href": href} for label, href in pages], "breadcrumbs": ["dashboard", "timeline", "segment", "recommendation", "evidence", "optimization_path"], "segment_anchors": anchors, "actions": ["back_to_dashboard", "open_related_recommendation", "open_source_segment", "open_evidence_artifact", "compare_this_segment", "view_optimization_path"], "summary": {"persistent_link_count": len(pages), "segment_anchor_count": len(anchors)}, "limitations": [LIMITATION]})
    return output

