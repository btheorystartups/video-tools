"""Deterministic transition confidence and continuity analysis."""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from stability import deterministic_id


EVIDENCE_WEIGHTS = {
    "transcript_pause": 0.2,
    "rhetorical_shift": 0.18,
    "topic_shift": 0.2,
    "acoustic_energy_change": 0.14,
    "pacing_shift": 0.13,
    "emotional_transition": 0.15,
}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _confidence_class(score: float) -> str:
    if score >= 0.74:
        return "high"
    if score >= 0.56:
        return "moderate"
    if score >= 0.38:
        return "weak"
    return "ambiguous"


def _transition_id(left: dict, right: dict) -> str:
    return deterministic_id("TRN", left.get("segment_id"), right.get("segment_id"), left.get("end_sec"), right.get("start_sec"))


def _by_pair(rows: list[dict], left_key: str, right_key: str) -> dict[tuple[str, str], dict]:
    return {(row.get(left_key), row.get(right_key)): row for row in rows}


def _by_segment(rows: list[dict]) -> dict[str, dict]:
    return {row.get("segment_id"): row for row in rows if row.get("segment_id")}


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


def build_transition_confidence(
    scene_segments: dict,
    audio_features: dict,
    acoustic_features: dict | None,
    topic_analysis: dict | None,
    rhetorical_analysis: dict | None,
    emotional_arc: dict | None,
) -> dict:
    """Fuse visible local evidence into per-boundary transition confidence."""

    segments = scene_segments.get("segments") or []
    acoustic_features = acoustic_features or {}
    topic_analysis = topic_analysis or {}
    rhetorical_analysis = rhetorical_analysis or {}
    emotional_arc = emotional_arc or {}
    topic_pairs = _by_pair(topic_analysis.get("segment_to_segment_topic_continuity") or [], "from_segment_id", "to_segment_id")
    rhetoric_pairs = _by_pair(rhetorical_analysis.get("rhetorical_transitions") or [], "from_segment_id", "to_segment_id")
    acoustic_pairs = _by_pair(acoustic_features.get("acoustic_contrast_between_segments") or [], "from_segment_id", "to_segment_id")
    emotional_by_id = _by_segment(emotional_arc.get("segments") or [])
    acoustic_summary_mean = _num((acoustic_features.get("rms_energy_summary") or {}).get("mean"), 0.0)

    transitions = []
    for index, (left, right) in enumerate(zip(segments, segments[1:]), start=1):
        left_id = left.get("segment_id")
        right_id = right.get("segment_id")
        pair = (left_id, right_id)
        gap = max(0.0, _num(right.get("start_sec")) - _num(left.get("end_sec")))
        transcript_pause = _clamp(gap / 2.2)

        topic_row = topic_pairs.get(pair, {})
        topic_shift = _clamp(topic_row.get("shift_likelihood", 0.35 if not topic_row else 0.0))
        rhetoric_row = rhetoric_pairs.get(pair, {})
        if rhetoric_row:
            rhetorical_shift = 0.72 if rhetoric_row.get("transition_type") == "mode_shift" else 0.18
        else:
            left_markers = set(left.get("topic_markers") or [])
            right_markers = set(right.get("topic_markers") or [])
            rhetorical_shift = 0.5 if left_markers != right_markers and (left_markers or right_markers) else 0.25

        acoustic_row = acoustic_pairs.get(pair, {})
        contrast = acoustic_row.get("energy_contrast")
        if contrast is None:
            acoustic_shift = 0.35
        else:
            acoustic_shift = _clamp(_num(contrast) / max(acoustic_summary_mean * 1.4, 0.001))

        pacing_shift = _clamp(abs(_num(right.get("speech_rate_wpm")) - _num(left.get("speech_rate_wpm"))) / 130.0)
        left_arc = emotional_by_id.get(left_id, {})
        right_arc = emotional_by_id.get(right_id, {})
        emotional_shift = _clamp(
            (
                abs(_num(right_arc.get("energy"), 0.5) - _num(left_arc.get("energy"), 0.5))
                + abs(_num(right_arc.get("valence"), 0.5) - _num(left_arc.get("valence"), 0.5))
                + abs(_num(right_arc.get("intensity"), 0.5) - _num(left_arc.get("intensity"), 0.5))
            )
            / 1.35
        )
        if left_arc and right_arc and left_arc.get("dominant_tone") != right_arc.get("dominant_tone"):
            emotional_shift = _clamp(emotional_shift + 0.18)

        signals = {
            "transcript_pause": transcript_pause,
            "rhetorical_shift": _clamp(rhetorical_shift),
            "topic_shift": topic_shift,
            "acoustic_energy_change": acoustic_shift,
            "pacing_shift": pacing_shift,
            "emotional_transition": emotional_shift,
        }
        weighted = sum(signals[key] * EVIDENCE_WEIGHTS[key] for key in EVIDENCE_WEIGHTS)
        active_weight = sum(EVIDENCE_WEIGHTS.values())
        confidence = _clamp(weighted / max(active_weight, 1e-9))
        support = [
            {"modality": key, "score": value}
            for key, value in signals.items()
            if value >= 0.55
        ]
        conflict = [
            {"modality": key, "score": value}
            for key, value in signals.items()
            if value <= 0.28
        ]
        high_continuity = topic_shift <= 0.32 and signals["rhetorical_shift"] <= 0.32
        isolated_support = len(support) <= 1 and any(row["modality"] in {"transcript_pause", "pacing_shift", "acoustic_energy_change"} for row in support)
        likely_false = confidence < 0.5 and (high_continuity or isolated_support)
        continuity_override = high_continuity and any(row["modality"] in {"transcript_pause", "pacing_shift", "acoustic_energy_change"} for row in support)
        transition_id = _transition_id(left, right)
        transitions.append(
            {
                "transition_id": transition_id,
                "transition_index": index,
                "from_segment_id": left_id,
                "to_segment_id": right_id,
                "start_sec": left.get("end_sec"),
                "end_sec": right.get("start_sec"),
                "confidence_score": confidence,
                "confidence_class": _confidence_class(confidence),
                "supporting_evidence": support,
                "conflicting_evidence": conflict,
                "likely_true_transition": bool(confidence >= 0.56 and len(support) >= 2 and not continuity_override),
                "likely_false_positive": bool(likely_false),
                "continuity_override": bool(continuity_override),
                "evidence_weights": dict(EVIDENCE_WEIGHTS),
                "evidence_scores": signals,
                "reasoning_summary": _reasoning_summary(signals, support, conflict, continuity_override, likely_false),
            }
        )

    false_positive_boundaries = build_false_positive_boundaries(transitions)
    continuity_analysis = build_continuity_analysis(transitions)
    return {
        "analysis_status": "complete" if transitions else "limited",
        "method": "deterministic_multimodal_transition_confidence_v1",
        "transitions": transitions,
        "summary": {
            "transition_count": len(transitions),
            "confidence_distribution": _distribution([row.get("confidence_score") for row in transitions]),
            "likely_true_transition_count": sum(1 for row in transitions if row.get("likely_true_transition")),
            "likely_false_positive_count": sum(1 for row in transitions if row.get("likely_false_positive")),
            "continuity_override_count": sum(1 for row in transitions if row.get("continuity_override")),
        },
        "limitations": [
            "Transition confidence fuses deterministic local signals only.",
            "No boundary is removed automatically; false-positive flags are review evidence.",
        ],
        "false_positive_boundaries": false_positive_boundaries,
        "continuity_analysis": continuity_analysis,
    }


def build_false_positive_boundaries(transition_report: dict | list[dict]) -> dict:
    rows = transition_report if isinstance(transition_report, list) else transition_report.get("transitions", [])
    flags = []
    for row in rows:
        scores = row.get("evidence_scores") or {}
        support = {item.get("modality") for item in row.get("supporting_evidence", [])}
        topic_continuity = _clamp(1.0 - _num(scores.get("topic_shift"), 0.35))
        rhetorical_continuity = _clamp(1.0 - _num(scores.get("rhetorical_shift"), 0.35))
        pacing_only = support and support <= {"pacing_shift", "transcript_pause"} and topic_continuity >= 0.62 and rhetorical_continuity >= 0.62
        acoustic_only = support == {"acoustic_energy_change"} and topic_continuity >= 0.62
        weak_topic = _num(scores.get("topic_shift"), 0.35) < 0.42
        weak_rhetoric = _num(scores.get("rhetorical_shift"), 0.35) < 0.42
        likely_false = bool(row.get("likely_false_positive") or pacing_only or acoustic_only)
        flags.append(
            {
                "transition_id": row.get("transition_id"),
                "from_segment_id": row.get("from_segment_id"),
                "to_segment_id": row.get("to_segment_id"),
                "likely_false_boundary": likely_false,
                "weak_transition": row.get("confidence_class") in {"weak", "ambiguous"},
                "pacing_only_transition": bool(pacing_only),
                "transcript_pause_only_transition": bool(support == {"transcript_pause"}),
                "isolated_acoustic_spike": bool(acoustic_only),
                "weak_topic_evidence": bool(weak_topic),
                "weak_rhetorical_evidence": bool(weak_rhetoric),
                "rhetorical_continuity_override": bool(rhetorical_continuity >= 0.68 and _num(scores.get("rhetorical_shift"), 0) <= 0.32),
                "topic_continuity_override": bool(topic_continuity >= 0.68 and _num(scores.get("topic_shift"), 0) <= 0.32),
                "false_positive_probability": _clamp(0.25 + (0.35 if likely_false else 0.0) + (0.18 if pacing_only else 0.0) + (0.12 if weak_topic and weak_rhetoric else 0.0) - (_num(row.get("confidence_score")) * 0.25)),
                "evidence": row.get("evidence_scores", {}),
            }
        )
    return {
        "analysis_status": "complete" if rows else "limited",
        "false_positive_boundary_count": sum(1 for row in flags if row["likely_false_boundary"]),
        "boundary_count": len(flags),
        "false_positive_boundary_ratio": round(sum(1 for row in flags if row["likely_false_boundary"]) / max(len(flags), 1), 3),
        "boundaries": flags,
        "limitations": ["Boundaries are flagged for review only and are never removed automatically."],
    }


def build_continuity_analysis(transition_report: dict | list[dict]) -> dict:
    rows = transition_report if isinstance(transition_report, list) else transition_report.get("transitions", [])
    continuity_rows = []
    for row in rows:
        scores = row.get("evidence_scores") or {}
        modality = {
            "topic_continuity": _clamp(1.0 - _num(scores.get("topic_shift"), 0.35)),
            "rhetorical_continuity": _clamp(1.0 - _num(scores.get("rhetorical_shift"), 0.35)),
            "emotional_continuity": _clamp(1.0 - _num(scores.get("emotional_transition"), 0.35)),
            "pacing_continuity": _clamp(1.0 - _num(scores.get("pacing_shift"), 0.35)),
            "acoustic_continuity": _clamp(1.0 - _num(scores.get("acoustic_energy_change"), 0.35)),
        }
        values = list(modality.values())
        cross_modal_agreement = _clamp(1.0 - ((pstdev(values) if len(values) > 1 else 0.0) * 1.7))
        continuity_rows.append(
            {
                "transition_id": row.get("transition_id"),
                "from_segment_id": row.get("from_segment_id"),
                "to_segment_id": row.get("to_segment_id"),
                **modality,
                "cross_modal_continuity_agreement": cross_modal_agreement,
                "continuity_confidence": _clamp(mean(values) * 0.68 + cross_modal_agreement * 0.32),
                "notes": _continuity_notes(modality),
            }
        )
    return {
        "analysis_status": "complete" if rows else "limited",
        "continuity_rows": continuity_rows,
        "summary": {
            "transition_count": len(continuity_rows),
            "mean_topic_continuity": _distribution([row["topic_continuity"] for row in continuity_rows]).get("mean"),
            "mean_rhetorical_continuity": _distribution([row["rhetorical_continuity"] for row in continuity_rows]).get("mean"),
            "mean_cross_modal_continuity_agreement": _distribution([row["cross_modal_continuity_agreement"] for row in continuity_rows]).get("mean"),
        },
        "limitations": [
            "Continuity measures agreement among observable heuristic signals.",
            "Continuity is not a semantic truth guarantee.",
        ],
    }


def _reasoning_summary(signals: dict, support: list[dict], conflict: list[dict], continuity_override: bool, likely_false: bool) -> str:
    top = sorted(signals.items(), key=lambda item: (-item[1], item[0]))[:2]
    low = sorted(signals.items(), key=lambda item: (item[1], item[0]))[:2]
    parts = [f"strongest signals: {', '.join(f'{key}={value}' for key, value in top)}"]
    parts.append(f"weakest signals: {', '.join(f'{key}={value}' for key, value in low)}")
    if continuity_override:
        parts.append("topic/rhetorical continuity reduces boundary confidence")
    if likely_false:
        parts.append("flagged for false-positive boundary review")
    if support and conflict:
        parts.append("modalities disagree")
    return "; ".join(parts) + "."


def _continuity_notes(modality: dict) -> list[str]:
    ordered = sorted(modality.items(), key=lambda item: item[1])
    notes = [f"lowest continuity: {ordered[0][0]}={ordered[0][1]}"]
    if modality["topic_continuity"] < 0.45 and modality["rhetorical_continuity"] >= 0.65:
        notes.append("Topic drift exists while rhetorical continuity remains comparatively high.")
    if modality["pacing_continuity"] < 0.45 and modality["topic_continuity"] >= 0.65:
        notes.append("Pacing shift is stronger than topic shift; review for false-positive segmentation.")
    return notes
