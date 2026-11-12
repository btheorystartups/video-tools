"""Configurable audio extraction for audio-analysis packets."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_UNAVAILABLE, utc_now_iso


SUPPORTED_AUDIO_FORMATS = {"wav", "mp3", "m4a"}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_ffmpeg_audio_command(
    ffmpeg: str,
    source_video: Path,
    output_path: Path,
    *,
    audio_format: str = "wav",
    sample_rate: int = 16000,
    mono: bool = True,
) -> list[str]:
    if audio_format not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {audio_format}")
    command = [ffmpeg, "-y", "-i", str(source_video), "-vn"]
    if mono:
        command.extend(["-ac", "1"])
    command.extend(["-ar", str(sample_rate)])
    if audio_format == "wav":
        command.extend(["-f", "wav"])
    elif audio_format == "mp3":
        command.extend(["-codec:a", "libmp3lame", "-b:a", "128k"])
    elif audio_format == "m4a":
        command.extend(["-codec:a", "aac", "-b:a", "128k"])
    command.append(str(output_path))
    return command


def extract_audio_artifact(
    source_video: Path,
    output_root: Path,
    *,
    audio_format: str = "wav",
    sample_rate: int = 16000,
    mono: bool = True,
) -> dict:
    """Extract audio into ``output_root/audio`` and write metadata/log JSON."""

    if audio_format not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {audio_format}")
    audio_dir = output_root / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / f"extracted_audio.{audio_format}"
    metadata_path = audio_dir / "extracted_audio_metadata.json"
    log_path = audio_dir / "audio_extraction_log.json"
    ffmpeg = shutil.which("ffmpeg")
    warnings: list[str] = []
    errors: list[str] = []
    command: list[str] = []
    stderr_tail = ""

    if not ffmpeg:
        errors.append("ffmpeg executable was not found on PATH.")
        status = STATUS_UNAVAILABLE
    else:
        command = build_ffmpeg_audio_command(
            ffmpeg,
            source_video,
            output_path,
            audio_format=audio_format,
            sample_rate=sample_rate,
            mono=mono,
        )
        try:
            completed = subprocess.run(command, check=True, capture_output=True, text=True)
            stderr_tail = (completed.stderr or "")[-2000:]
            status = STATUS_COMPLETE
        except subprocess.CalledProcessError as exc:
            stderr_tail = (exc.stderr or "")[-4000:]
            errors.append("ffmpeg audio extraction failed.")
            status = STATUS_ERROR

    exists = output_path.exists()
    metadata = {
        "generated_at_utc": utc_now_iso(),
        "source_video_path": source_video.name,
        "extracted_audio_path": f"audio/{output_path.name}" if exists else None,
        "format": audio_format,
        "sample_rate": sample_rate,
        "channels": 1 if mono else None,
        "duration_seconds": None,
        "file_size_bytes": output_path.stat().st_size if exists else 0,
        "sha256": sha256_file(output_path) if exists else None,
        "ffmpeg_available": bool(ffmpeg),
        "ffmpeg_command": " ".join(command) if command else None,
        "extraction_status": status,
        "warnings": warnings,
        "errors": errors,
    }
    log = {
        "generated_at_utc": metadata["generated_at_utc"],
        "status": status,
        "command": command,
        "stderr_tail": stderr_tail,
        "warnings": warnings,
        "errors": errors,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": status, "audio_path": str(output_path) if exists else None, "metadata": metadata, "log": log}
