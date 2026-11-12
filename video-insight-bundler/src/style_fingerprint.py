"""Editorial structure style fingerprinting, not identity recognition."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, clamp, deterministic_id, sorted_segments


def build_style_fingerprint(analyses: list[dict]) -> dict:
    rows = []
    for analysis in analyses:
        segments = sorted_segments(analysis.get("scene_segments") or {})
        sequence = analysis.get("sequence_structure") or {}
        pressure = analysis.get("editorial_pressure") or {}
        visual = analysis.get("visual_structure") or {}
        readiness = analysis.get("release_readiness") or {}
        rates = [segment.get("speech_rate_wpm") for segment in segments if segment.get("speech_rate_wpm") is not None]
        rows.append(
            {
                "fingerprint_id": deterministic_id("STYLE", analysis.get("analysis_dir"), [row.get("segment_id") for row in segments]),
                "analysis_dir": analysis.get("analysis_dir"),
                "pacing_signature": avg([float(value) / 220.0 for value in rates]) if rates else 0.0,
                "continuity_signature": readiness.get("score_components", {}).get("ambiguity_adjusted_continuity") or (sequence.get("summary") or {}).get("structural_coherence_score"),
                "rhetorical_density": avg([len(row.get("topic_markers") or []) / 4.0 for row in segments]),
                "transition_density": (sequence.get("summary") or {}).get("transition_density"),
                "callback_density": (analysis.get("callback_resolution") or {}).get("callback_strength_score"),
                "discourse_density": (analysis.get("discourse_state") or {}).get("discourse_pressure_score"),
                "contradiction_tendency": clamp(1.0 - (readiness.get("score_components", {}).get("contradiction_cluster_pressure") or 0.65)),
                "ambiguity_tendency": clamp(1.0 - (readiness.get("score_components", {}).get("ambiguity_adjusted_continuity") or 0.5)),
                "visual_continuity_signature": visual.get("visual_continuity_score"),
                "structural_rhythm_signature": (pressure.get("summary") or {}).get("peak_cumulative_pressure_score"),
            }
        )
    output = base_artifact(method="deterministic_editorial_style_fingerprint_v1")
    output.update(
        {
            "style_fingerprints": rows,
            "style_fingerprint_id": deterministic_id("STYLESET", [row.get("fingerprint_id") for row in rows]),
            "summary": {
                "analysis_count": len(rows),
                "mean_pacing_signature": avg([row.get("pacing_signature") for row in rows]),
                "mean_transition_density": avg([row.get("transition_density") for row in rows]),
                "mean_structural_rhythm_signature": avg([row.get("structural_rhythm_signature") for row in rows]),
            },
        }
    )
    return output
