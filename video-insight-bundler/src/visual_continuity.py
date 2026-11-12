"""Deterministic visual continuity evidence summaries."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED, deterministic_id


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _distribution(values: list[float]) -> dict:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None, "stddev": None}
    return {
        "count": len(clean),
        "min": round(min(clean), 3),
        "max": round(max(clean), 3),
        "mean": round(mean(clean), 3),
        "stddev": round(pstdev(clean), 3) if len(clean) > 1 else 0.0,
    }


def _stability_regions(samples: list[dict], max_change: float = 0.18, min_samples: int = 3) -> list[dict]:
    regions = []
    current: list[dict] = []
    for row in samples:
        if _num(row.get("visual_change_score"), 0.0) <= max_change:
            current.append(row)
        else:
            if len(current) >= min_samples:
                regions.append(_region(current, len(regions) + 1))
            current = []
    if len(current) >= min_samples:
        regions.append(_region(current, len(regions) + 1))
    return regions


def _region(rows: list[dict], index: int) -> dict:
    start = _num(rows[0].get("timestamp_sec"))
    end = _num(rows[-1].get("timestamp_sec"), start)
    return {
        "region_id": deterministic_id("VSTAB", index, f"{start:.3f}", f"{end:.3f}"),
        "start_sec": round(start, 3),
        "end_sec": round(end, 3),
        "duration_sec": round(max(end - start, 0.0), 3),
        "sample_count": len(rows),
        "mean_similarity": _clamp(mean([_num(row.get("frame_similarity_to_previous"), 1.0) for row in rows])),
        "mean_change_intensity": _clamp(mean([_num(row.get("visual_change_score"), 0.0) for row in rows])),
    }


def analyze_visual_continuity(shot_boundaries: dict, composition_features: dict, scene_segments: dict) -> dict:
    """Measure local pixel/color/edge continuity over time."""

    samples = shot_boundaries.get("sampled_frame_features") or []
    boundaries = shot_boundaries.get("detected_boundaries") or []
    segments = scene_segments.get("segments") or []
    changes = [_num(row.get("visual_change_score"), 0.0) for row in samples[1:]]
    similarities = [_num(row.get("frame_similarity_to_previous"), 1.0) for row in samples[1:]]
    duration = max([_num(row.get("end_sec")) for row in segments] + [_num(samples[-1].get("timestamp_sec")) if samples else 0.0, 1.0])
    boundary_rate = len(boundaries) / max(duration / 60.0, 1e-9)
    stability_regions = _stability_regions(samples)
    abrupt = [
        {
            "transition_id": row.get("boundary_id"),
            "timestamp_sec": row.get("timestamp_sec"),
            "visual_change_score": row.get("visual_change_score"),
            "boundary_confidence": row.get("boundary_confidence"),
            "neighboring_frame_paths": row.get("neighboring_frame_paths", []),
        }
        for row in boundaries
    ]
    reset_candidates = [
        {
            "reset_candidate_id": deterministic_id("VRESET", row.get("boundary_id"), row.get("timestamp_sec")),
            "shot_boundary_id": row.get("boundary_id"),
            "timestamp_sec": row.get("timestamp_sec"),
            "visual_reset_strength": _clamp(_num(row.get("visual_change_score")) * 0.65 + _num(row.get("boundary_confidence")) * 0.35),
            "review_action": "Review as possible visual reset point; do not rewrite transcript or timing automatically.",
            "limitations": ["Reset candidates are visual-change evidence only, not intent claims."],
        }
        for row in boundaries
        if _num(row.get("boundary_confidence")) >= 0.58
    ]
    continuity_score = _clamp(
        (mean(similarities) if similarities else 0.35) * 0.54
        + (1.0 - min(boundary_rate / 18.0, 1.0)) * 0.2
        + (1.0 - min((pstdev(changes) if len(changes) > 1 else 0.0) * 2.0, 1.0)) * 0.16
        + min(len(stability_regions) / max(len(segments), 1), 1.0) * 0.1
    )
    return {
        "analysis_status": STATUS_COMPLETE if samples else STATUS_LIMITED,
        "method": "deterministic_visual_continuity_v1",
        "visual_change_intensity": [
            {
                "sample_id": row.get("sample_id"),
                "timestamp_sec": row.get("timestamp_sec"),
                "visual_change_score": row.get("visual_change_score"),
                "frame_similarity_to_previous": row.get("frame_similarity_to_previous"),
            }
            for row in samples
        ],
        "visual_stability_regions": stability_regions,
        "abrupt_visual_transitions": abrupt,
        "sustained_visual_similarity": {
            "mean_similarity": round(mean(similarities), 3) if similarities else None,
            "high_similarity_sample_count": sum(1 for value in similarities if value >= 0.82),
        },
        "visual_pacing": {
            "shot_boundary_count": len(boundaries),
            "shot_boundaries_per_minute": round(boundary_rate, 3),
            "mean_change_intensity": round(mean(changes), 3) if changes else None,
        },
        "visual_reset_candidates": reset_candidates,
        "visual_continuity_score": continuity_score,
        "composition_context": {
            "mean_complexity": ((composition_features.get("summary") or {}).get("visual_complexity") or {}).get("mean"),
            "mean_motion_proxy": ((composition_features.get("summary") or {}).get("motion_proxy") or {}).get("mean"),
        },
        "summary": {
            "sample_count": len(samples),
            "shot_boundary_count": len(boundaries),
            "stability_region_count": len(stability_regions),
            "reset_candidate_count": len(reset_candidates),
            "change_distribution": _distribution(changes),
        },
        "limitations": [
            "Continuity is based only on sampled pixel/color/edge changes.",
            "No semantic object, face, identity, emotion, or cinematic intent detection is performed.",
        ],
    }
