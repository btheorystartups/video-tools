"""Deterministic frame and segment-level composition feature summaries."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED


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


def _segment_for(timestamp: float, segments: list[dict]) -> dict | None:
    for segment in segments:
        if _num(segment.get("start_sec")) <= timestamp <= _num(segment.get("end_sec")):
            return segment
    return None


def _negative_space_proxy(row: dict) -> float:
    low_edge = 1.0 - _num(row.get("edge_density"), 0.0)
    low_complexity = 1.0 - _num(row.get("visual_complexity"), 0.0)
    low_contrast = 1.0 - min(_num(row.get("contrast"), 0.0), 1.0)
    return _clamp(low_edge * 0.45 + low_complexity * 0.35 + low_contrast * 0.2)


def analyze_composition_features(shot_boundaries: dict, scene_segments: dict) -> dict:
    """Summarize deterministic brightness/color/edge/motion features."""

    samples = [dict(row) for row in shot_boundaries.get("sampled_frame_features") or []]
    segments = scene_segments.get("segments") or []
    frame_features = []
    for row in samples:
        timestamp = _num(row.get("timestamp_sec"))
        segment = _segment_for(timestamp, segments)
        motion_proxy = _num(row.get("visual_change_score"), 0.0)
        frame_features.append(
            {
                "sample_id": row.get("sample_id"),
                "timestamp_sec": row.get("timestamp_sec"),
                "segment_id": segment.get("segment_id") if segment else None,
                "brightness": _num(row.get("brightness")),
                "contrast": _num(row.get("contrast")),
                "saturation_proxy": _num(row.get("saturation_proxy")),
                "edge_density": _num(row.get("edge_density")),
                "visual_complexity": _num(row.get("visual_complexity")),
                "motion_proxy": _clamp(motion_proxy),
                "negative_space_proxy": _negative_space_proxy(row),
                "frame_similarity_to_previous": _num(row.get("frame_similarity_to_previous"), 1.0),
            }
        )

    segment_summaries = []
    for segment in segments:
        sid = segment.get("segment_id")
        rows = [row for row in frame_features if row.get("segment_id") == sid]
        complexities = [row["visual_complexity"] for row in rows]
        motion = [row["motion_proxy"] for row in rows]
        stillness = [1.0 - row["motion_proxy"] for row in rows]
        abruptness = [row["motion_proxy"] for row in rows if row["motion_proxy"] >= 0.46]
        segment_summaries.append(
            {
                "segment_id": sid,
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "sample_count": len(rows),
                "mean_complexity": round(mean(complexities), 3) if complexities else None,
                "complexity_variance": round(pstdev(complexities) ** 2, 4) if len(complexities) > 1 else 0.0 if complexities else None,
                "visual_energy": _clamp(mean([_num(row["visual_complexity"]) * 0.58 + _num(row["motion_proxy"]) * 0.42 for row in rows])) if rows else None,
                "visual_stillness": _clamp(mean(stillness)) if stillness else None,
                "abruptness": _clamp(max(abruptness) if abruptness else 0.0),
                "limitations": ["Segment summaries depend on sampled frames and may miss between-sample changes."],
            }
        )

    return {
        "analysis_status": STATUS_COMPLETE if frame_features else STATUS_LIMITED,
        "method": "deterministic_frame_composition_features_v1",
        "frame_features": frame_features,
        "segment_summaries": segment_summaries,
        "summary": {
            "sample_count": len(frame_features),
            "brightness": _distribution([row["brightness"] for row in frame_features]),
            "contrast": _distribution([row["contrast"] for row in frame_features]),
            "saturation_proxy": _distribution([row["saturation_proxy"] for row in frame_features]),
            "edge_density": _distribution([row["edge_density"] for row in frame_features]),
            "visual_complexity": _distribution([row["visual_complexity"] for row in frame_features]),
            "motion_proxy": _distribution([row["motion_proxy"] for row in frame_features]),
            "negative_space_proxy": _distribution([row["negative_space_proxy"] for row in frame_features]),
        },
        "limitations": [
            "Composition features are deterministic pixel/color/edge summaries.",
            "No face, identity, emotion, object, or intent interpretation is performed.",
        ],
    }
