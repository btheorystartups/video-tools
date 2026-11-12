"""Rule-based narrative phase modeling without semantic runtime."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id, num, segment_rate, sorted_segments


PHASES = ["introduction", "framing", "exploration", "escalation", "expansion", "reflection", "synthesis", "reinforcement", "conclusion", "unresolved_exit"]


def _phase_for(index: int, total: int, segment: dict, rhythm: dict) -> str:
    position = index / max(total - 1, 1)
    markers = set(segment.get("topic_markers") or [])
    text = (segment.get("text") or "").lower()
    wave = rhythm.get("wave_class")
    if index == 0:
        return "introduction"
    if position < 0.2:
        return "framing" if markers & {"causal", "sequence"} else "exploration"
    if wave in {"pacing_acceleration", "density_spike"} and position < 0.75:
        return "escalation"
    if markers & {"example", "instruction"} and position < 0.82:
        return "expansion"
    if "because" in text or "therefore" in text or markers & {"causal"}:
        return "synthesis"
    if position > 0.86:
        if text.strip().endswith("?") or segment.get("word_count", 0) < 14:
            return "unresolved_exit"
        return "conclusion"
    if segment_rate(segment) < 95:
        return "reflection"
    return "reinforcement"


def build_narrative_phase_model(bundle, temporal_rhythm: dict | None = None) -> dict:
    segments = sorted_segments(bundle.scene_segments)
    rhythm_by_id = {row.get("segment_id"): row for row in (temporal_rhythm or {}).get("rhythm_segments", [])}
    rows = []
    for index, segment in enumerate(segments):
        rhythm = rhythm_by_id.get(segment.get("segment_id"), {})
        phase = _phase_for(index, len(segments), segment, rhythm)
        confidence = clamp(0.46 + min(len(segment.get("topic_markers") or []) * 0.08, 0.22) + (0.12 if rhythm else 0.0) + (0.08 if index in {0, len(segments) - 1} else 0.0))
        rows.append(
            {
                "phase_id": deterministic_id("PHASE", segment.get("segment_id"), phase, index),
                "segment_id": segment.get("segment_id"),
                "phase": phase,
                "phase_index": index + 1,
                "position_ratio": round(index / max(len(segments) - 1, 1), 3),
                "phase_confidence": confidence,
                "supporting_evidence": {
                    "topic_markers": segment.get("topic_markers") or [],
                    "wave_class": rhythm.get("wave_class"),
                    "word_count": segment.get("word_count"),
                    "speech_rate_wpm": segment.get("speech_rate_wpm"),
                },
            }
        )
    phase_counts = {phase: sum(1 for row in rows if row["phase"] == phase) for phase in PHASES}
    output = base_artifact(method="deterministic_narrative_phase_model_v1")
    output.update(
        {
            "phase_segments": rows,
            "phase_sequence": [row["phase"] for row in rows],
            "summary": {
                "segment_count": len(rows),
                "phase_counts": {key: value for key, value in phase_counts.items() if value},
                "unresolved_exit_count": phase_counts.get("unresolved_exit", 0),
                "phase_coverage_score": clamp(len([v for v in phase_counts.values() if v]) / 6.0),
                "mean_phase_confidence": round(sum(num(row["phase_confidence"]) for row in rows) / max(len(rows), 1), 3),
            },
        }
    )
    return output
