"""Scene hierarchy scaffolding from deterministic segment structure."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, deterministic_id, marker_counts, num, sorted_segments


def build_scene_hierarchy(bundle, sequence_structure: dict | None = None) -> dict:
    segments = sorted_segments(bundle.scene_segments)
    groups = (sequence_structure or {}).get("segment_groups") or []
    if not groups and segments:
        groups = [
            {
                "group_id": deterministic_id("SGRP", "all", [row.get("segment_id") for row in segments]),
                "segment_ids": [row.get("segment_id") for row in segments],
                "start_sec": segments[0].get("start_sec"),
                "end_sec": segments[-1].get("end_sec"),
                "group_class": "single_sequence",
            }
        ]
    scenes = []
    for index, group in enumerate(groups, start=1):
        ids = set(group.get("segment_ids") or [])
        group_segments = [row for row in segments if row.get("segment_id") in ids]
        markers = marker_counts(group_segments)
        scenes.append(
            {
                "scene_id": deterministic_id("SCN", group.get("group_id"), index),
                "parent_sequence_group_id": group.get("group_id"),
                "scene_index": index,
                "segment_ids": [row.get("segment_id") for row in group_segments],
                "start_sec": group.get("start_sec"),
                "end_sec": group.get("end_sec"),
                "duration_sec": round(num(group.get("end_sec")) - num(group.get("start_sec")), 3),
                "hierarchy_level": 1,
                "scene_role": group.get("group_class", "sequence_region"),
                "dominant_markers": [key for key, _ in markers.most_common(4)],
                "mean_segment_coherence": avg([num(row.get("segment_coherence_score"), 0.35) for row in group_segments]),
            }
        )
    output = base_artifact(method="deterministic_scene_hierarchy_v1")
    output.update(
        {
            "hierarchy_root_id": deterministic_id("HIER", [row.get("segment_id") for row in segments]),
            "scenes": scenes,
            "summary": {
                "scene_count": len(scenes),
                "segment_count": len(segments),
                "mean_scene_coherence": avg([row["mean_segment_coherence"] for row in scenes]),
                "hierarchy_depth": 1 if scenes else 0,
            },
        }
    )
    return output
