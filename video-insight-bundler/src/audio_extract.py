"""Audio extraction helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_UNAVAILABLE


def _write_log(evidence_dir: Path | None, text: str) -> None:
    if evidence_dir:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        (evidence_dir / "ffmpeg_audio_extract.log").write_text(text, encoding="utf-8")


def extract_audio(video_path: Path, audio_output_path: Path, evidence_dir: Path | None = None) -> dict:
    """Extract mono 16 kHz WAV audio for local transcription and pacing analysis."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        result = {"status": STATUS_UNAVAILABLE, "reason": "ffmpeg executable was not found on PATH.", "audio_path": None}
        _write_log(evidence_dir, result["reason"])
        return result

    audio_output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(audio_output_path),
    ]
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        log = "\n".join(["COMMAND: " + " ".join(cmd), "STDOUT:", exc.stdout or "", "STDERR:", exc.stderr or ""])
        _write_log(evidence_dir, log)
        return {
            "status": STATUS_ERROR,
            "reason": "ffmpeg audio extraction failed",
            "stderr": exc.stderr[-2000:],
            "audio_path": None,
        }
    _write_log(
        evidence_dir,
        "\n".join(["COMMAND: " + " ".join(cmd), "STDOUT:", completed.stdout or "", "STDERR:", completed.stderr or ""]),
    )
    return {
        "status": STATUS_COMPLETE,
        "audio_path": str(audio_output_path),
        "command": " ".join(cmd),
        "stderr_tail": completed.stderr[-1000:],
    }
