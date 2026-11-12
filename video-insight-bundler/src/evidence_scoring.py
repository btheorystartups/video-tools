"""Deterministic evidence strength scoring for local analysis artifacts."""

from __future__ import annotations

from statistics import mean
from typing import Any


MODALITY_KEYS = [
    "transcript",
    "segmentation",
    "acoustic",
    "rhetorical",
    "topic",
    "emotional",
    "visual",
    "recommendation",
    "revision",
]


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _status_score(status: Any) -> float:
    return {
        "complete": 1.0,
        "limited": 0.62,
        "skipped": 0.32,
        "unavailable": 0.25,
        "error": 0.1,
    }.get(str(status or ""), 0.35)


def _avg(values: list[float]) -> float:
    clean = [float(value) for value in values if value is not None]
    return round(mean(clean), 3) if clean else 0.0


def _numeric(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _class(score: float) -> str:
    if score >= 0.78:
        return "strong"
    if score >= 0.58:
        return "moderate"
    if score >= 0.38:
        return "weak"
    return "limited"


def build_evidence_score_summary(bundle, transition_confidence: dict | None = None, revision_data: dict | None = None) -> dict:
    """Score the strength of each evidence family without inferring semantic certainty."""

    segments = bundle.scene_segments.get("segments") or []
    transcript_segments = bundle.transcript.get("segments") or []
    acoustic = getattr(bundle, "acoustic_features", None) or {}
    topic = getattr(bundle, "topic_analysis", None) or {}
    rhetoric = getattr(bundle, "rhetorical_analysis", None) or {}
    emotional = bundle.emotional_arc or {}
    visual_structure = getattr(bundle, "visual_structure", None) or {}
    visual_continuity = getattr(bundle, "visual_continuity", None) or {}
    visual_alignment = getattr(bundle, "visual_boundary_alignment", None) or {}
    recommendations = (getattr(bundle, "recommendations_json", None) or {}).get("recommendations") or []

    boundary_values = [
        _numeric(segment.get("boundary_confidence"), _numeric((segment.get("boundary") or {}).get("confidence"), 0.0))
        for segment in segments
    ]
    questionable_ratio = sum(1 for segment in segments if (segment.get("boundary") or {}).get("questionable")) / max(len(segments), 1)
    topic_rows = topic.get("per_segment_keywords") or []
    topic_continuity = topic.get("segment_to_segment_topic_continuity") or []
    rhetoric_rows = rhetoric.get("segments") or []
    acoustic_rows = acoustic.get("segments") or []
    emotional_rows = emotional.get("segments") or []
    transition_rows = (transition_confidence or {}).get("transitions") or []

    transcript_score = _clamp(
        _status_score(bundle.transcript.get("transcription_status")) * 0.52
        + min(len(transcript_segments) / max(len(segments), 1), 1.0) * 0.18
        + min(_numeric(bundle.audio_features.get("word_count")) / 900.0, 1.0) * 0.2
        + (0.1 if bundle.transcript.get("text") else 0.0)
    )
    segmentation_score = _clamp(_avg(boundary_values) * 0.68 + (1.0 - questionable_ratio) * 0.22 + min(len(segments) / 4.0, 1.0) * 0.1)
    acoustic_score = _clamp(
        _status_score(acoustic.get("analysis_status")) * 0.62
        + min(len(acoustic_rows) / max(len(segments), 1), 1.0) * 0.2
        + (0.18 if acoustic.get("rms_energy_summary", {}).get("count") else 0.0)
    )
    rhetorical_score = _clamp(
        _status_score(rhetoric.get("analysis_status")) * 0.54
        + min(len(rhetoric_rows) / max(len(segments), 1), 1.0) * 0.22
        + _numeric(rhetoric.get("rhetorical_balance_score"), 0.35) * 0.24
    )
    topic_score = _clamp(
        _status_score(topic.get("analysis_status")) * 0.48
        + min(len(topic_rows) / max(len(segments), 1), 1.0) * 0.2
        + (1.0 - _numeric(topic.get("topic_drift_score"), 0.65)) * 0.22
        + min(len(topic_continuity) / max(len(segments) - 1, 1), 1.0) * 0.1
    )
    emotional_score = _clamp(
        _status_score(emotional.get("analysis_status")) * 0.55
        + min(len(emotional_rows) / max(len(segments), 1), 1.0) * 0.25
        + min(sum(len(row.get("evidence") or []) for row in emotional_rows) / max(len(emotional_rows) * 3, 1), 1.0) * 0.2
    )
    visual_score = _clamp(
        _status_score(visual_structure.get("analysis_status")) * 0.34
        + _numeric(visual_structure.get("visual_evidence_completeness"), 0.0) * 0.28
        + _numeric(visual_continuity.get("visual_continuity_score"), 0.35) * 0.18
        + _numeric(visual_structure.get("visual_boundary_alignment_quality"), 0.35) * 0.14
        + (1.0 - _numeric((visual_alignment.get("summary") or {}).get("mean_visual_contradiction"), 0.35)) * 0.06
    )
    recommendation_score = _clamp(
        _status_score((getattr(bundle, "recommendations_json", None) or {}).get("recommendation_status")) * 0.42
        + min(len(recommendations) / 5.0, 1.0) * 0.22
        + _avg([_numeric(row.get("confidence")) for row in recommendations]) * 0.26
        + min(sum(len(row.get("evidence") or []) for row in recommendations) / max(len(recommendations) * 3, 1), 1.0) * 0.1
    )
    revision_status = (revision_data or {}).get("status")
    revision_score = _clamp(
        _status_score(revision_status) * 0.42
        + (0.24 if (revision_data or {}).get("revision_candidates") else 0.0)
        + (0.18 if (revision_data or {}).get("mutation_safety_contract") else 0.0)
        + (0.16 if (revision_data or {}).get("branch_comparison") else 0.0)
    ) if revision_data else 0.35

    transition_quality = _avg([_numeric(row.get("confidence_score")) for row in transition_rows]) if transition_rows else None
    modality_scores = {
        "transcript": transcript_score,
        "segmentation": segmentation_score,
        "acoustic": acoustic_score,
        "rhetorical": rhetorical_score,
        "topic": topic_score,
        "emotional": emotional_score,
        "visual": visual_score,
        "recommendation": recommendation_score,
        "revision": revision_score,
    }
    overall = _avg(list(modality_scores.values()))
    weak = [{"modality": key, "score": value, "class": _class(value)} for key, value in sorted(modality_scores.items(), key=lambda item: (item[1], item[0]))[:4]]
    strong = [{"modality": key, "score": value, "class": _class(value)} for key, value in sorted(modality_scores.items(), key=lambda item: (-item[1], item[0]))[:4]]

    return {
        "analysis_status": "complete",
        "method": "deterministic_visible_artifact_evidence_strength_v1",
        "overall_evidence_strength": overall,
        "overall_evidence_class": _class(overall),
        "modality_scores": {
            key: {
                "score": value,
                "score_class": _class(value),
                "notes": _notes_for(key, value),
            }
            for key, value in modality_scores.items()
        },
        "transition_evidence_quality": transition_quality,
        "strongest_evidence": strong,
        "weakest_evidence": weak,
        "score_inputs": {
            "segment_count": len(segments),
            "transcript_segment_count": len(transcript_segments),
            "questionable_boundary_ratio": round(questionable_ratio, 3),
            "recommendation_count": len(recommendations),
            "transition_count": len(transition_rows),
            "visual_sample_count": len((getattr(bundle, "shot_boundaries", None) or {}).get("sampled_frame_features") or []),
            "visual_boundary_count": len((getattr(bundle, "shot_boundaries", None) or {}).get("detected_boundaries") or []),
        },
        "limitations": [
            "Evidence strength measures availability, consistency, and grounding of local artifacts.",
            "Scores do not assert semantic truth or editorial correctness.",
        ],
    }


def _notes_for(modality: str, score: float) -> list[str]:
    base = {
        "transcript": "Transcript strength increases with complete local transcript text and timed segments.",
        "segmentation": "Segmentation strength uses boundary confidence and questionable-boundary ratio.",
        "acoustic": "Acoustic strength depends on local waveform energy features.",
        "rhetorical": "Rhetorical strength uses deterministic marker coverage and balance.",
        "topic": "Topic strength uses deterministic keyword continuity, not embeddings.",
        "emotional": "Emotional strength uses transparent lexical and pacing cues.",
        "visual": "Visual strength uses local deterministic pixel/color/edge summaries and boundary alignment.",
        "recommendation": "Recommendation strength uses evidence counts and confidence grounding.",
        "revision": "Revision strength uses proposal artifact completeness and safety metadata.",
    }[modality]
    if score < 0.4:
        return [base, "Current evidence is weak or partially unavailable."]
    if score < 0.65:
        return [base, "Current evidence is usable but should be reviewed alongside other modalities."]
    return [base, "Current evidence is comparatively well grounded for deterministic review."]
