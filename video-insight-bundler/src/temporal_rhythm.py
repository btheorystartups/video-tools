"""Deterministic temporal rhythm and pacing-wave analysis."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, clamp, deterministic_id, distribution, num, segment_center, segment_rate, sorted_segments, transition_pairs


def _wave_class(delta: float, density: float) -> str:
    if delta >= 0.18:
        return "pacing_acceleration"
    if delta <= -0.18:
        return "pacing_slowdown"
    if density >= 0.72:
        return "density_spike"
    if density <= 0.24:
        return "pause_or_low_density"
    return "steady_cadence"


def build_temporal_rhythm(bundle) -> dict:
    segments = sorted_segments(bundle.scene_segments)
    rows = []
    rates = [segment_rate(row) for row in segments]
    max_rate = max(rates or [1.0])
    for index, segment in enumerate(segments):
        prev_rate = rates[index - 1] if index > 0 else rates[index]
        rate = rates[index]
        next_rate = rates[index + 1] if index + 1 < len(rates) else rate
        density = clamp(rate / max(max_rate, 1.0))
        acceleration = clamp((rate - prev_rate) / max(max_rate, 1.0) * 0.5 + 0.5)
        slowdown = clamp((prev_rate - rate) / max(max_rate, 1.0))
        rhetorical_markers = len(segment.get("topic_markers") or [])
        compression = clamp((density * 0.72) + min(rhetorical_markers / 4.0, 1.0) * 0.28)
        expansion = clamp((1.0 - density) * 0.66 + min(num(segment.get("duration_sec")) / 45.0, 1.0) * 0.34)
        delta = (next_rate - prev_rate) / max(max_rate, 1.0)
        intensity = clamp(density * 0.45 + abs(delta) * 0.35 + min(rhetorical_markers / 3.0, 1.0) * 0.2)
        rows.append(
            {
                "rhythm_id": deterministic_id("RHY", segment.get("segment_id"), rate, prev_rate, next_rate),
                "segment_id": segment.get("segment_id"),
                "start_sec": segment.get("start_sec"),
                "end_sec": segment.get("end_sec"),
                "center_sec": segment_center(segment),
                "speech_rate_wpm": round(rate, 3),
                "density_score": density,
                "acceleration_score": acceleration,
                "slowdown_score": slowdown,
                "rhetorical_compression": compression,
                "rhetorical_expansion": expansion,
                "intensity_wave_score": intensity,
                "wave_class": _wave_class(delta, density),
                "evidence": {
                    "previous_wpm": round(prev_rate, 3),
                    "next_wpm": round(next_rate, 3),
                    "topic_marker_count": rhetorical_markers,
                    "duration_sec": segment.get("duration_sec"),
                },
            }
        )
    transition_rows = []
    for left, right in transition_pairs(segments):
        cadence = clamp(abs(segment_rate(right) - segment_rate(left)) / max(max_rate, 1.0))
        transition_rows.append(
            {
                "cadence_id": deterministic_id("CAD", left.get("segment_id"), right.get("segment_id")),
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "transition_cadence_score": cadence,
                "cadence_class": "abrupt" if cadence >= 0.42 else "moderate" if cadence >= 0.2 else "smooth",
            }
        )
    output = base_artifact(method="deterministic_temporal_rhythm_v1")
    output.update(
        {
            "rhythm_segments": rows,
            "transition_cadence": transition_rows,
            "summary": {
                "segment_count": len(rows),
                "pacing_acceleration_count": sum(1 for row in rows if row["wave_class"] == "pacing_acceleration"),
                "pacing_slowdown_count": sum(1 for row in rows if row["wave_class"] == "pacing_slowdown"),
                "density_spike_count": sum(1 for row in rows if row["wave_class"] == "density_spike"),
                "pause_region_count": sum(1 for row in rows if row["wave_class"] == "pause_or_low_density"),
                "mean_intensity_wave_score": avg([row["intensity_wave_score"] for row in rows]),
                "speech_rate_distribution": distribution(rates),
                "mean_transition_cadence": avg([row["transition_cadence_score"] for row in transition_rows]),
            },
        }
    )
    return output
