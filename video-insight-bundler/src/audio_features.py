"""Transcript-derived pacing and pause analysis."""

from __future__ import annotations

import re
from statistics import mean

WORD_RE = re.compile(r"\b[\w']+\b")


def _count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def analyze_audio_features(transcript: dict, media_metadata: dict, audio_result: dict) -> dict:
    segments = transcript.get("segments") or []
    duration = media_metadata.get("duration_sec") or transcript.get("duration") or 0.0
    word_count = _count_words(transcript.get("text", ""))
    speech_minutes = max(float(duration or 0.0) / 60.0, 1e-9)
    segment_features = []
    pause_features = []

    previous_end = None
    for index, segment in enumerate(segments):
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        text = segment.get("text", "")
        words = _count_words(text)
        seg_duration = max(end - start, 0.001)
        if previous_end is not None:
            gap = max(start - previous_end, 0.0)
            if gap >= 0.25:
                pause_features.append(
                    {
                        "after_segment_index": index - 1,
                        "start_sec": round(previous_end, 3),
                        "end_sec": round(start, 3),
                        "duration_sec": round(gap, 3),
                    }
                )
        segment_features.append(
            {
                "segment_index": index,
                "start_sec": round(start, 3),
                "end_sec": round(end, 3),
                "duration_sec": round(seg_duration, 3),
                "word_count": words,
                "words_per_minute": round(words / (seg_duration / 60.0), 2),
            }
        )
        previous_end = end

    rates = [feature["words_per_minute"] for feature in segment_features if feature["word_count"] > 0]
    pauses = [pause["duration_sec"] for pause in pause_features]
    return {
        "analysis_status": "complete" if segments else "limited",
        "basis": "transcript timestamps" if segments else "media duration only",
        "audio_extraction_status": audio_result.get("status"),
        "transcription_status": transcript.get("transcription_status"),
        "duration_sec": duration,
        "word_count": word_count,
        "overall_words_per_minute": round(word_count / speech_minutes, 2) if duration else None,
        "segment_speech_rate": segment_features,
        "pauses": pause_features,
        "pause_count": len(pause_features),
        "total_pause_sec": round(sum(pauses), 3),
        "average_pause_sec": round(mean(pauses), 3) if pauses else 0.0,
        "average_segment_words_per_minute": round(mean(rates), 2) if rates else None,
        "limitations": [
            "Speech rate and pauses are derived from transcript timestamps, not acoustic phoneme analysis."
        ],
    }
