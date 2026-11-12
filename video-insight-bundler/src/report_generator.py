"""Quality and statistics reports for generated analysis bundles."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from statistics import mean, median, pstdev

try:
    import textstat
except Exception:  # pragma: no cover - optional dependency
    textstat = None

WORD_RE = re.compile(r"\b[\w']+\b")
QUESTION_RE = re.compile(r"\?")
MARKERS = {
    "contrast": ["but", "however", "instead", "whereas"],
    "causal": ["because", "therefore", "so", "as a result"],
    "sequence": ["first", "second", "third", "next", "finally", "then"],
    "example": ["for example", "for instance", "imagine", "suppose"],
    "instructional": ["should", "need", "must", "do this", "you can"],
    "analytical": ["because", "evidence", "data", "pattern", "system", "model"],
}
STOPWORDS = {
    "the", "and", "that", "this", "with", "you", "for", "are", "but", "have", "was", "were",
    "from", "not", "they", "your", "its", "into", "can", "all", "any", "why", "how", "what",
    "when", "then", "than", "much", "more", "will", "would", "could", "should", "there",
}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def words(text: str) -> list[str]:
    return [item.lower() for item in WORD_RE.findall(text or "")]


def keyword_counts(text: str, limit: int = 40) -> list[dict]:
    counts = Counter(token for token in words(text) if len(token) > 2 and token not in STOPWORDS)
    return [{"term": term, "count": count} for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def marker_counts(text: str) -> dict:
    lowered = (text or "").lower()
    return {
        label: sum(lowered.count(marker) for marker in markers)
        for label, markers in MARKERS.items()
    }


def _distribution(values: list[float]) -> dict:
    values = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "stddev": None}
    return {
        "count": len(values),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "mean": round(mean(values), 3),
        "median": round(median(values), 3),
        "stddev": round(pstdev(values), 3) if len(values) > 1 else 0.0,
    }


def _score(value: float | None, target: tuple[float, float], hard: tuple[float, float]) -> float:
    if value is None:
        return 0.35
    low, high = target
    hard_low, hard_high = hard
    if low <= value <= high:
        return 1.0
    if value < low:
        return max(0.0, 1.0 - ((low - value) / max(low - hard_low, 1e-9)))
    return max(0.0, 1.0 - ((value - high) / max(hard_high - high, 1e-9)))


def build_report_data(bundle) -> dict:
    transcript_text = bundle.transcript.get("text", "")
    transcript_segments = bundle.transcript.get("segments") or []
    scene_segments = bundle.scene_segments.get("segments") or []
    speech_rates = [item.get("words_per_minute") for item in bundle.audio_features.get("segment_speech_rate", [])]
    pause_durations = [item.get("duration_sec") for item in bundle.audio_features.get("pauses", [])]
    segment_durations = [item.get("duration_sec") for item in scene_segments]
    emotional = bundle.emotional_arc.get("segments") or []
    acoustic = getattr(bundle, "acoustic_features", None) or {}
    topic = getattr(bundle, "topic_analysis", None) or {}
    rhetoric = getattr(bundle, "rhetorical_analysis", None) or {}
    topic_continuity = getattr(bundle, "topic_continuity", None) or {}
    rhetorical_coherence = getattr(bundle, "rhetorical_coherence", None) or {}
    boundary_diagnostics = getattr(bundle, "boundary_diagnostics", None) or {}
    discourse_summary = getattr(bundle, "discourse_summary", None) or {}
    intensity = [item.get("intensity") for item in emotional]
    valence = [item.get("valence") for item in emotional]
    tones = Counter(item.get("dominant_tone", "neutral") for item in emotional)
    markers = marker_counts(transcript_text)
    questions = len(QUESTION_RE.findall(transcript_text))
    keyword_list = keyword_counts(transcript_text)
    readability = None
    if textstat and transcript_text.strip():
        try:
            readability = round(float(textstat.flesch_reading_ease(transcript_text)), 3)
        except Exception:
            readability = None

    rate_dist = _distribution([float(rate) for rate in speech_rates if rate is not None])
    pause_dist = _distribution([float(pause) for pause in pause_durations if pause is not None])
    segment_dist = _distribution([float(duration) for duration in segment_durations if duration is not None])
    transcript_quality = round(
        min(1.0, 0.35 + (0.35 if bundle.transcript.get("transcription_status") == "complete" else 0.0)
            + min(len(transcript_segments) / 20.0, 0.2) + min((bundle.audio_features.get("word_count") or 0) / 1000.0, 0.1)),
        3,
    )
    pacing_consistency = round(_score(rate_dist.get("stddev"), (0, 65), (0, 160)), 3)
    segmentation_smoothness = round(_score(segment_dist.get("stddev"), (0, 25), (0, 90)), 3)
    emotional_continuity = round(_score(_distribution(valence).get("stddev"), (0, 0.18), (0, 0.5)), 3)
    rhetorical_consistency = round(_score(_distribution(list(markers.values())).get("stddev"), (0, 6), (0, 20)), 3)
    recommendation_confidence = round(mean([
        transcript_quality,
        pacing_consistency,
        1.0 if scene_segments else 0.3,
        1.0 if emotional else 0.4,
    ]), 3)

    warnings = list(bundle.warnings)
    if not transcript_text.strip():
        warnings.append({"code": "REPORT_NO_TRANSCRIPT_TEXT", "severity": "warning", "message": "Transcript text is missing; language-derived reports are limited."})
    if not pause_durations:
        warnings.append({"code": "REPORT_NO_PAUSES", "severity": "info", "message": "No transcript-timed pauses were detected."})

    return {
        "report_version": "1.0",
        "source_video": bundle.source_video,
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "quality_scores": {
            "transcript_quality": transcript_quality,
            "pacing_consistency": pacing_consistency,
            "segmentation_smoothness": segmentation_smoothness,
            "emotional_continuity": emotional_continuity,
            "rhetorical_consistency": rhetorical_consistency,
            "recommendation_confidence": recommendation_confidence,
        },
        "transcript_statistics": {
            "status": bundle.transcript.get("transcription_status"),
            "word_count": bundle.audio_features.get("word_count"),
            "segment_count": len(transcript_segments),
            "question_count": questions,
            "readability_flesch": readability,
            "top_keywords": keyword_list,
        },
        "rhetorical_statistics": {
            "marker_counts": markers,
            "question_density_per_100_words": round(questions / max((bundle.audio_features.get("word_count") or 0), 1) * 100.0, 3),
            "instructional_to_analytical_ratio": round((markers["instructional"] + 1) / (markers["analytical"] + 1), 3),
        },
        "rhetorical_deep_dive": rhetoric,
        "segment_statistics": {
            "segment_count": len(scene_segments),
            "duration_distribution": segment_dist,
            "confidence_distribution": _distribution([1.0 if item.get("text") else 0.35 for item in scene_segments]),
        },
        "segment_boundary_report": {
            "segment_count": len(scene_segments),
            "boundary_confidence_distribution": _distribution([item.get("boundary_confidence") for item in scene_segments]),
            "questionable_boundaries": [
                {
                    "segment_id": item.get("segment_id"),
                    "start_sec": item.get("start_sec"),
                    "end_sec": item.get("end_sec"),
                    "boundary": item.get("boundary"),
                }
                for item in scene_segments
                if (item.get("boundary") or {}).get("questionable")
            ],
            "transition_type_counts": dict(sorted(Counter((item.get("boundary") or {}).get("transition_type", "unknown") for item in scene_segments).items())),
            "limitations": ["Boundary confidence is a deterministic heuristic for review, not shot-boundary detection."],
        },
        "pacing_statistics": {
            "overall_words_per_minute": bundle.audio_features.get("overall_words_per_minute"),
            "speaking_rate_distribution": rate_dist,
            "pause_distribution": pause_dist,
            "pacing_volatility": rate_dist.get("stddev"),
        },
        "acoustic_statistics": {
            "status": acoustic.get("analysis_status"),
            "silence_ratio": acoustic.get("silence_ratio"),
            "rms_energy_summary": acoustic.get("rms_energy_summary"),
            "energy_variability": acoustic.get("energy_variability"),
            "spectral_centroid_summary": acoustic.get("spectral_centroid_summary"),
            "zero_crossing_rate_summary": acoustic.get("zero_crossing_rate_summary"),
            "loudness_energy_trend": acoustic.get("loudness_energy_trend"),
            "limitations": acoustic.get("limitations", []),
        },
        "topic_statistics": {
            "status": topic.get("analysis_status"),
            "method": topic.get("method"),
            "topic_drift_score": topic.get("topic_drift_score"),
            "top_global_keywords": topic.get("top_global_keywords", []),
            "tfidf_weighted_terms": topic.get("tfidf_weighted_terms", []),
            "likely_topic_shift_count": len(topic.get("likely_topic_shifts", []) or []),
            "limitations": topic.get("limitations", []),
            "topic_continuity_score": topic_continuity.get("topic_continuity_score"),
            "unsupported_topic_shift_count": len(topic_continuity.get("unsupported_topic_shifts") or []),
        },
        "continuity_statistics": {
            "topic_continuity": topic_continuity,
            "rhetorical_coherence": rhetorical_coherence,
            "boundary_diagnostics_summary": boundary_diagnostics.get("summary", {}),
            "discourse_summary": discourse_summary,
        },
        "emotional_statistics": {
            "tone_counts": dict(sorted(tones.items())),
            "intensity_distribution": _distribution(intensity),
            "valence_distribution": _distribution(valence),
        },
        "warnings": warnings,
        "limitations": bundle.profile.get("limitations", []) + [
            "Quality scores are transparent heuristics intended to prioritize human review.",
            "Pacing and pause features are transcript-timing derived unless acoustic analysis is added later.",
        ],
    }


def write_reports(bundle) -> dict:
    reports_dir = bundle.output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    data = build_report_data(bundle)
    _write_json(reports_dir / "quality_report.json", data)
    _write_json(reports_dir / "transcript_statistics.json", data["transcript_statistics"])
    _write_json(reports_dir / "rhetorical_statistics.json", data["rhetorical_statistics"])
    _write_json(reports_dir / "rhetorical_deep_dive.json", data["rhetorical_deep_dive"])
    _write_json(reports_dir / "segment_statistics.json", data["segment_statistics"])
    _write_json(reports_dir / "segment_boundary_report.json", data["segment_boundary_report"])
    _write_json(reports_dir / "pacing_statistics.json", data["pacing_statistics"])
    _write_json(reports_dir / "acoustic_statistics.json", data["acoustic_statistics"])
    _write_json(reports_dir / "topic_statistics.json", data["topic_statistics"])
    _write_json(reports_dir / "continuity_statistics.json", data["continuity_statistics"])

    lines = [
        "# Quality Report",
        "",
        "Generated from local analysis artifacts using transparent deterministic heuristics.",
        "",
        "## Quality Scores",
        "",
    ]
    for label, value in data["quality_scores"].items():
        lines.append(f"- {label.replace('_', ' ').title()}: `{value}`")
    lines.extend(["", "## Warnings", ""])
    if data["warnings"]:
        for item in data["warnings"]:
            lines.append(f"- `{item.get('code')}` ({item.get('severity', 'warning')}): {item.get('message')}")
    else:
        lines.append("- No quality warnings.")
    lines.extend([
        "",
        "## Transcript",
        "",
        f"- Status: `{data['transcript_statistics']['status']}`",
        f"- Words: `{data['transcript_statistics']['word_count']}`",
        f"- Questions: `{data['transcript_statistics']['question_count']}`",
        f"- Flesch reading ease: `{data['transcript_statistics']['readability_flesch']}`",
        "",
        "## Pacing",
        "",
        f"- Overall WPM: `{data['pacing_statistics']['overall_words_per_minute']}`",
        f"- Pacing volatility: `{data['pacing_statistics']['pacing_volatility']}`",
        "",
        "## Limitations",
        "",
    ])
    lines.extend(f"- {item}" for item in data["limitations"])
    (reports_dir / "quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return data
