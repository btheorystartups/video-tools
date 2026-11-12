"""Media metadata extraction using FFprobe plus local file metadata."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_UNAVAILABLE, write_json


def _run_ffprobe(video_path: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        result = {"status": STATUS_UNAVAILABLE, "reason": "ffprobe executable was not found on PATH."}
        if evidence_dir:
            write_json(evidence_dir / "ffprobe_raw_output.json", result)
        return result

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        result = {
            "status": STATUS_ERROR,
            "reason": "ffprobe failed",
            "stderr": exc.stderr.strip(),
        }
        if evidence_dir:
            write_json(evidence_dir / "ffprobe_raw_output.json", result)
        return result
    raw = json.loads(completed.stdout)
    result = {"status": STATUS_COMPLETE, "command": cmd, "raw": raw}
    if evidence_dir:
        write_json(evidence_dir / "ffprobe_raw_output.json", result)
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_fraction(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            denominator_float = float(denominator)
            if denominator_float == 0:
                return None
            return float(numerator) / denominator_float
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, "N/A"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, "N/A"):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def probe_media(video_path: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    """Return JSON-safe metadata for a local video file."""
    stat = video_path.stat()
    ffprobe_result = _run_ffprobe(video_path, evidence_dir)
    raw = ffprobe_result.get("raw", {}) if ffprobe_result.get("status") == STATUS_COMPLETE else {}
    streams = raw.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    format_info = raw.get("format", {})

    duration = _safe_float(format_info.get("duration")) or _safe_float(video_stream.get("duration"))
    fps = _parse_fraction(video_stream.get("avg_frame_rate")) or _parse_fraction(video_stream.get("r_frame_rate"))
    frame_count = _safe_int(video_stream.get("nb_frames"))
    if frame_count is None and duration and fps:
        frame_count = int(round(duration * fps))

    return {
        "source_path": str(video_path),
        "file_name": video_path.name,
        "file_size_bytes": stat.st_size,
        "sha256": _sha256(video_path),
        "probe_status": ffprobe_result.get("status"),
        "probe_reason": ffprobe_result.get("reason"),
        "duration_sec": duration,
        "fps": fps,
        "frame_count": frame_count,
        "width": _safe_int(video_stream.get("width")),
        "height": _safe_int(video_stream.get("height")),
        "video_codec": video_stream.get("codec_name"),
        "video_profile": video_stream.get("profile"),
        "pix_fmt": video_stream.get("pix_fmt"),
        "audio_codec": audio_stream.get("codec_name"),
        "audio_sample_rate": _safe_int(audio_stream.get("sample_rate")),
        "audio_channels": _safe_int(audio_stream.get("channels")),
        "format_name": format_info.get("format_name"),
        "bit_rate": _safe_int(format_info.get("bit_rate")),
    }
