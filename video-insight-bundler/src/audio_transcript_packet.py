"""Transcript packet export for audio-analysis packages."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from stability import STATUS_COMPLETE, STATUS_UNAVAILABLE, utc_now_iso

WORD_RE = re.compile(r"\b[\w']+\b")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def load_transcript_artifact(analysis_root: Path, source_video: Path | None = None) -> tuple[dict, Path | None]:
    candidates = [analysis_root / "transcript.json"]
    manifest_path = analysis_root / "corpus" / "corpus_run_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in manifest.get("per_video_output_dirs") or []:
                path = Path(item) / "transcript.json"
                if path.exists():
                    candidates.append(path)
        except Exception:
            pass
    if source_video:
        candidates.append(source_video.parent / f"{source_video.stem}_analysis" / "transcript.json")
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), path
    return {"transcription_status": STATUS_UNAVAILABLE, "text": "", "segments": [], "reason": "No transcript artifact was found."}, None


def build_transcript_packet(analysis_root: Path, output_root: Path, source_video: Path | None = None) -> dict:
    audio_analysis = output_root / "audio_analysis"
    audio_analysis.mkdir(parents=True, exist_ok=True)
    transcript, source_path = load_transcript_artifact(analysis_root, source_video)
    segments = transcript.get("segments") or []
    text = transcript.get("text") or " ".join(str(row.get("text", "")).strip() for row in segments).strip()
    rows = []
    for index, segment in enumerate(segments):
        start = float(segment.get("start", segment.get("start_sec", 0.0)) or 0.0)
        end = float(segment.get("end", segment.get("end_sec", start)) or start)
        segment_text = str(segment.get("text", "")).strip()
        words = count_words(segment_text)
        duration = max(end - start, 0.0)
        rows.append(
            {
                "segment_id": segment.get("id", segment.get("segment_id", index)),
                "start_sec": round(start, 3),
                "end_sec": round(end, 3),
                "duration_sec": round(duration, 3),
                "speaker": segment.get("speaker"),
                "text": segment_text,
                "word_count": words,
                "wpm": round(words / max(duration / 60.0, 1e-9), 2) if duration and words else 0.0,
                "confidence": segment.get("confidence", segment.get("avg_logprob")),
            }
        )
    available = bool(text.strip() or rows)
    report = {
        "generated_at_utc": utc_now_iso(),
        "transcript_available": available,
        "transcription_status": transcript.get("transcription_status"),
        "source_transcript_artifact": source_path.name if source_path else None,
        "segment_count": len(rows),
        "word_count": count_words(text),
        "warnings": [] if available else ["transcript_required_for_full_pacing_analysis"],
        "limitations": ["Transcript text is reused from local artifacts only; missing text is not invented."],
    }
    (audio_analysis / "transcript_full.md").write_text("# Transcript\n\n" + (text or "[No transcript text available.]") + "\n", encoding="utf-8")
    (audio_analysis / "transcript_full.txt").write_text(text + ("\n" if text else ""), encoding="utf-8")
    (audio_analysis / "transcript_segments.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (audio_analysis / "timed_transcript.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    for name in ("transcript_segments.csv", "timed_transcript.csv"):
        with (audio_analysis / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["segment_id", "start_sec", "end_sec", "duration_sec", "speaker", "word_count", "wpm", "confidence", "text"])
            writer.writeheader()
            writer.writerows(rows)
    (audio_analysis / "transcript_availability_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if not available:
        (audio_analysis / "transcript_missing_report.md").write_text(
            "# Transcript Missing\n\nNo transcript artifact was found. Full pacing analysis requires transcript timing; audio-only metrics continue where possible.\n",
            encoding="utf-8",
        )
    return {"transcript": {"text": text, "segments": rows, "transcription_status": transcript.get("transcription_status")}, "report": report}
