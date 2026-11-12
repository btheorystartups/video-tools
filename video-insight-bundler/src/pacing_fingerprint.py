"""Recurring pacing signature analysis."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, deterministic_id, distribution, sorted_segments


def build_pacing_fingerprint(analyses: list[dict]) -> dict:
    rows = []
    for analysis in analyses:
        segments = sorted_segments(analysis.get("scene_segments") or {})
        rates = [row.get("speech_rate_wpm") for row in segments if row.get("speech_rate_wpm") is not None]
        rhythm = analysis.get("temporal_rhythm") or {}
        rows.append(
            {
                "pacing_fingerprint_id": deterministic_id("PACEFP", analysis.get("analysis_dir"), rates),
                "analysis_dir": analysis.get("analysis_dir"),
                "speech_rate_distribution": distribution(rates),
                "pacing_wave_profile": (rhythm.get("summary") or {}).get("mean_intensity_wave_score"),
                "acceleration_count": (rhythm.get("summary") or {}).get("pacing_acceleration_count"),
                "slowdown_count": (rhythm.get("summary") or {}).get("pacing_slowdown_count"),
                "pause_region_count": (rhythm.get("summary") or {}).get("pause_region_count"),
            }
        )
    output = base_artifact(method="deterministic_pacing_fingerprint_v1")
    output.update({"pacing_fingerprints": rows, "summary": {"analysis_count": len(rows), "mean_wave_profile": avg([row.get("pacing_wave_profile") for row in rows])}})
    return output
