"""Deterministic overlay filter metadata for static local consoles."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


FILTERS = [
    "severity",
    "confidence",
    "overlay_type",
    "subsystem",
    "recommendation_linked_only",
    "blocker_linked_only",
    "high_effort_only",
    "low_effort_high_impact_only",
    "segment_id",
    "video_id",
    "profile_benchmark_type",
]


def build_overlay_filter_registry(overlays: dict, lanes: dict, traceability: dict, profile_packs: dict | None = None) -> dict:
    rec_ids = {row.get("recommendation_id") for row in traceability.get("traceability_entries") or []}
    lane_by_video = {(row.get("video_id"), row.get("lane_key")): row.get("lane_id") for row in lanes.get("lanes") or []}
    items = []
    for overlay in overlays.get("overlays") or []:
        overlay_type = overlay.get("overlay_type") or "unknown"
        lane_key = overlay_type.replace("_overlay", "")
        rec_linked = bool(set(overlay.get("related_recommendations") or []) & rec_ids) or overlay_type == "recommendation_overlay"
        blocker_linked = overlay_type == "blocker_overlay" or bool(overlay.get("related_recommendations") and overlay.get("severity") == "high")
        items.append(
            {
                "filter_item_id": deterministic_id("OFILT", overlay.get("overlay_id")),
                "overlay_id": overlay.get("overlay_id"),
                "video_id": overlay.get("video_id"),
                "segment_id": overlay.get("segment_id"),
                "severity": overlay.get("severity"),
                "confidence": overlay.get("confidence"),
                "overlay_type": overlay_type,
                "subsystem": lane_key,
                "lane_id": lane_by_video.get((overlay.get("video_id"), lane_key)),
                "recommendation_linked": rec_linked,
                "blocker_linked": blocker_linked,
                "high_effort": False,
                "low_effort_high_impact": rec_linked and overlay.get("severity") in {"high", "medium"},
                "profile_benchmark_type": "local_corpus",
            }
        )
    counts = Counter(item["severity"] for item in items)
    output = base_artifact(method="deterministic_overlay_filtering_v1")
    output.update(
        {
            "overlay_filter_registry_id": deterministic_id("OFILTREG", [(row["overlay_id"], row["severity"]) for row in items]),
            "filters": FILTERS,
            "filter_items": items,
            "ui_controls": ["toggle_all", "show_high_severity_only", "show_recommendations_only", "show_blockers_only", "show_lane_group", "reset_filters"],
            "summary": {"filter_item_count": len(items), "severity_counts": dict(counts)},
            "limitations": [LIMITATION],
        }
    )
    return output
