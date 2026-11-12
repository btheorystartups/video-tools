"""Import externally produced transcripts without changing the native shape."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_segment(segment: dict, index: int) -> dict:
    return {
        "id": segment.get("id", index),
        "start": _safe_float(segment.get("start", segment.get("start_sec", 0.0))),
        "end": _safe_float(segment.get("end", segment.get("end_sec", segment.get("start", 0.0)))),
        "text": str(segment.get("text", "")).strip(),
        "avg_logprob": segment.get("avg_logprob"),
        "no_speech_prob": segment.get("no_speech_prob"),
    }


def import_transcript(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise ValueError("Transcript import must be a JSON object.")

    raw_segments = raw.get("segments") or []
    if not isinstance(raw_segments, list):
        raise ValueError("Transcript import 'segments' must be a list when present.")

    segments = [_normalize_segment(segment, index) for index, segment in enumerate(raw_segments) if isinstance(segment, dict)]
    text = str(raw.get("text") or " ".join(segment["text"] for segment in segments if segment.get("text"))).strip()
    native = "transcription_status" in raw
    status = raw.get("transcription_status") if native else (STATUS_COMPLETE if text or segments else STATUS_LIMITED)
    if status not in {STATUS_COMPLETE, STATUS_LIMITED, "unavailable", "error", "skipped"}:
        status = STATUS_LIMITED

    transcript = dict(raw) if native else {}
    transcript.update(
        {
            "transcription_status": status,
            "engine": raw.get("engine", "transcript_import"),
            "text": text,
            "segments": segments,
            "provenance": {
                "source": "transcript_import",
                "format": "native_video_insight_bundler" if native else "openai_whisper_json",
                "path": str(path),
            },
        }
    )
    return transcript
