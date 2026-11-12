"""Scene and topic segmentation heuristics."""

from __future__ import annotations

import re

from stability import deterministic_id

TOPIC_MARKERS = {
    "contrast": ["but", "however", "instead", "on the other hand"],
    "sequence": ["first", "second", "third", "next", "finally", "then"],
    "causal": ["because", "therefore", "so that", "as a result"],
    "example": ["for example", "for instance", "imagine", "suppose"],
    "instruction": ["you should", "you need", "let's", "we can", "do this"],
}


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w']+\b", text.lower())


def _markers(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for marker_name, phrases in TOPIC_MARKERS.items():
        if any(phrase in lowered for phrase in phrases):
            found.append(marker_name)
    return found


def _segment_record(
    index: int,
    start: float,
    end: float,
    text: str,
    basis: str,
    source_hash: str | None,
    profile_hash: str | None,
) -> dict:
    words = _words(text)
    duration = max(end - start, 0.001)
    rounded_start = round(start, 3)
    rounded_end = round(end, 3)
    return {
        "segment_id": deterministic_id("SEG", source_hash or "", profile_hash or "", f"{rounded_start:.3f}", f"{rounded_end:.3f}"),
        "start_sec": rounded_start,
        "end_sec": rounded_end,
        "duration_sec": round(duration, 3),
        "title": _title_from_text(text, index),
        "basis": basis,
        "word_count": len(words),
        "speech_rate_wpm": round(len(words) / (duration / 60.0), 2) if words else 0.0,
        "topic_markers": _markers(text),
        "summary": _shorten(text, 260),
        "text": text.strip(),
        "boundary": {
            "transition_type": "fallback_boundary" if basis.startswith("fixed") else "transcript_boundary",
            "confidence": 0.55 if basis.startswith("fixed") else 0.72,
            "questionable": False,
        },
        "boundary_confidence": 0.55 if basis.startswith("fixed") else 0.72,
        "segment_coherence_score": _coherence_score(text),
    }


def _shorten(text: str, length: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= length:
        return cleaned
    return cleaned[: length - 3].rstrip() + "..."


def _title_from_text(text: str, index: int) -> str:
    cleaned = _shorten(text, 70)
    if not cleaned:
        return f"Timed window {index + 1}"
    return cleaned[0].upper() + cleaned[1:]


def _ends_sentence(text: str) -> bool:
    return bool((text or "").strip().endswith((".", "?", "!", '"', "'")))


def _coherence_score(text: str) -> float:
    tokens = _words(text)
    if not tokens:
        return 0.25
    unique_ratio = len(set(tokens)) / max(len(tokens), 1)
    marker_bonus = min(len(_markers(text)) * 0.08, 0.2)
    length_score = min(len(tokens) / 80.0, 1.0)
    return round(max(0.25, min(1.0, (1.0 - unique_ratio) * 0.35 + length_score * 0.45 + marker_bonus)), 3)


def _boundary_type(gap: float, text: str, current_duration: float, target_duration: float) -> tuple[str, float]:
    if gap >= 0.75:
        return "pause_boundary", min(0.98, 0.72 + gap / 8.0)
    if _markers(text):
        return "rhetorical_marker_boundary", 0.78
    if current_duration >= target_duration:
        return "topic_boundary", 0.64
    return "fallback_boundary", 0.45


def _smooth_short_segments(segments: list[dict], minimum_duration: float) -> list[dict]:
    if len(segments) < 2:
        return segments
    output: list[dict] = []
    pending = None
    for segment in segments:
        if pending is None:
            pending = dict(segment)
            continue
        if float(pending.get("duration_sec") or 0) < minimum_duration:
            merged_text = " ".join(part for part in [pending.get("text", ""), segment.get("text", "")] if part).strip()
            pending.update(
                {
                    "end_sec": segment.get("end_sec"),
                    "duration_sec": round(float(segment.get("end_sec") or 0) - float(pending.get("start_sec") or 0), 3),
                    "text": merged_text,
                    "summary": _shorten(merged_text, 260),
                    "word_count": len(_words(merged_text)),
                    "topic_markers": sorted(set((pending.get("topic_markers") or []) + (segment.get("topic_markers") or []))),
                    "boundary": {
                        "transition_type": "fallback_boundary",
                        "confidence": 0.5,
                        "questionable": True,
                        "reason": "Very short adjacent segment was smoothed into the next segment.",
                    },
                    "boundary_confidence": 0.5,
                    "segment_coherence_score": _coherence_score(merged_text),
                }
            )
            duration = max(float(pending.get("duration_sec") or 0), 0.001)
            pending["speech_rate_wpm"] = round(pending["word_count"] / (duration / 60.0), 2) if pending["word_count"] else 0.0
        else:
            output.append(pending)
            pending = dict(segment)
    if pending is not None:
        output.append(pending)
    return output


def _from_transcript(
    transcript_segments: list[dict],
    target_duration: float,
    pause_threshold: float,
    source_hash: str | None,
    profile_hash: str | None,
) -> list[dict]:
    grouped = []
    current = []
    current_start = None
    previous_end = None

    for segment in transcript_segments:
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        text = segment.get("text", "")
        current_duration = (end - current_start) if current_start is not None else 0.0
        gap = (start - previous_end) if previous_end is not None else 0.0
        marker_shift = bool(_markers(text)) and current_duration >= target_duration * 0.5
        sentence_ok = not current or _ends_sentence(current[-1].get("text", ""))
        should_close = bool(current) and (
            gap >= pause_threshold or marker_shift or (current_duration >= target_duration and sentence_ok)
        )
        if should_close:
            boundary_type, confidence = _boundary_type(gap, text, current_duration, target_duration)
            current[-1]["_boundary_type"] = boundary_type
            current[-1]["_boundary_confidence"] = round(confidence, 3)
            grouped.append(current)
            current = []
            current_start = None
        if current_start is None:
            current_start = start
        current.append(segment)
        previous_end = end
    if current:
        grouped.append(current)

    output = []
    for index, group in enumerate(grouped):
        start = float(group[0].get("start", 0.0))
        end = float(group[-1].get("end", start))
        text = " ".join(item.get("text", "").strip() for item in group).strip()
        record = _segment_record(index, start, end, text, "transcript_timestamps", source_hash, profile_hash)
        boundary_type = group[-1].get("_boundary_type", "fallback_boundary")
        confidence = float(group[-1].get("_boundary_confidence", 0.58))
        questionable = confidence < 0.6 or (text and not _ends_sentence(text))
        record["boundary"] = {
            "transition_type": boundary_type,
            "confidence": round(confidence, 3),
            "questionable": questionable,
        }
        if questionable:
            record["boundary"]["reason"] = "Boundary confidence is low or segment does not end cleanly at sentence punctuation."
        record["boundary_confidence"] = record["boundary"]["confidence"]
        output.append(record)
    return _smooth_short_segments(output, max(4.0, target_duration * 0.18))


def _time_windows(duration: float, window_sec: float, source_hash: str | None, profile_hash: str | None) -> list[dict]:
    if duration <= 0:
        return []
    output = []
    start = 0.0
    index = 0
    while start < duration:
        end = min(start + window_sec, duration)
        output.append(_segment_record(index, start, end, "", "fixed_time_window_no_transcript", source_hash, profile_hash))
        start = end
        index += 1
    return output


def build_segments(
    transcript: dict,
    media_metadata: dict,
    audio_features: dict,
    profile: dict,
    profile_hash: str | None = None,
) -> dict:
    transcript_segments = transcript.get("segments") or []
    target_duration = float(profile.get("segment_target_duration_sec", 45.0))
    pause_threshold = float(profile.get("pause_segment_break_sec", 1.5))
    duration = float(media_metadata.get("duration_sec") or 0.0)

    if transcript_segments:
        segments = _from_transcript(
            transcript_segments,
            target_duration,
            pause_threshold,
            media_metadata.get("sha256"),
            profile_hash,
        )
        method = "transcript_pause_topic_window_heuristic"
    else:
        segments = _time_windows(duration, target_duration, media_metadata.get("sha256"), profile_hash)
        method = "fixed_time_window_fallback"

    return {
        "segmentation_status": "complete" if segments else "limited",
        "method": method,
        "segment_count": len(segments),
        "segments": segments,
        "limitations": [
            "Scene boundaries are inferred from transcript timing and rhetorical markers unless no transcript exists.",
            "This is not shot-boundary detection."
        ],
    }
