"""Optional local transcription with faster-whisper."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _segment_to_dict(segment: object) -> dict:
    return {
        "id": getattr(segment, "id", None),
        "start": float(getattr(segment, "start", 0.0)),
        "end": float(getattr(segment, "end", 0.0)),
        "text": str(getattr(segment, "text", "")).strip(),
        "avg_logprob": getattr(segment, "avg_logprob", None),
        "no_speech_prob": getattr(segment, "no_speech_prob", None),
    }


def transcribe_audio(audio_path: Path, profile: dict) -> dict:
    """Transcribe audio if faster-whisper is installed; otherwise return an explicit stub."""
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        return {
            "transcription_status": "unavailable",
            "reason": f"faster-whisper is not importable in this Python environment: {exc}",
            "engine": "faster-whisper",
            "text": "",
            "segments": [],
        }

    whisper_config = profile.get("transcription", {})
    model_name = whisper_config.get("model", "base")
    device = whisper_config.get("device", "cpu")
    compute_type = whisper_config.get("compute_type", "int8")
    language = whisper_config.get("language")

    try:
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
        segments_iter, info = model.transcribe(str(audio_path), language=language, vad_filter=True)
        segments = [_segment_to_dict(segment) for segment in segments_iter]
    except Exception as exc:  # Local ML stacks fail in environment-specific ways.
        return {
            "transcription_status": "error",
            "reason": f"faster-whisper failed: {exc}",
            "engine": "faster-whisper",
            "text": "",
            "segments": [],
        }

    text = " ".join(segment["text"] for segment in segments if segment.get("text")).strip()
    return {
        "transcription_status": "complete",
        "engine": "faster-whisper",
        "model": model_name,
        "language": getattr(info, "language", language),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "text": text,
        "segments": segments,
    }


def write_srt(transcript: dict, output_path: Path) -> None:
    segments: Iterable[dict] = transcript.get("segments") or []
    lines: list[str] = []
    if transcript.get("transcription_status") != "complete":
        reason = transcript.get("reason", "Transcription was not available.")
        lines = ["1", "00:00:00,000 --> 00:00:00,000", f"[{reason}]", ""]
    else:
        for index, segment in enumerate(segments, start=1):
            text = (segment.get("text") or "").strip()
            if not text:
                continue
            lines.extend(
                [
                    str(index),
                    f"{_format_srt_time(float(segment.get('start', 0.0)))} --> {_format_srt_time(float(segment.get('end', 0.0)))}",
                    text,
                    "",
                ]
            )
    output_path.write_text("\n".join(lines), encoding="utf-8")
