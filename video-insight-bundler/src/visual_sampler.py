"""Frame sampling using FFmpeg."""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_LIMITED, STATUS_UNAVAILABLE, deterministic_id, write_json


def _timestamps(duration: float | None, interval: float) -> list[float]:
    if not duration or duration <= 0:
        return [0.0]
    interval = max(float(interval), 1.0)
    points = [0.0]
    current = interval
    while current < duration:
        points.append(round(current, 3))
        current += interval
    if duration > 5 and points[-1] < duration - 2:
        points.append(round(max(duration - 1, 0), 3))
    return points


def _append_log(evidence_dir: Path | None, text: str) -> None:
    if evidence_dir:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        with (evidence_dir / "ffmpeg_frame_sampling.log").open("a", encoding="utf-8") as handle:
            handle.write(text.rstrip() + "\n\n")


def sample_frames(
    video_path: Path,
    frames_dir: Path,
    media_metadata: dict,
    sample_interval: float,
    profile_hash: str | None = None,
    evidence_dir: Path | None = None,
) -> dict:
    ffmpeg = shutil.which("ffmpeg")
    frames_dir.mkdir(parents=True, exist_ok=True)
    duration = media_metadata.get("duration_sec")
    fps = media_metadata.get("fps") or 0
    requested = _timestamps(duration, sample_interval)
    records = []

    if not ffmpeg:
        result = {
            "sampling_status": STATUS_UNAVAILABLE,
            "reason": "ffmpeg executable was not found on PATH.",
            "sample_interval_sec": sample_interval,
            "samples": [],
        }
        if evidence_dir:
            write_json(evidence_dir / "sampling_logs.json", result)
        return result

    for index, timestamp in enumerate(requested):
        frame_name = f"frame_{index:04d}_{int(timestamp * 1000):010d}ms.jpg"
        frame_path = frames_dir / frame_name
        cmd = [
            ffmpeg,
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(frame_path),
        ]
        try:
            completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
            status = STATUS_COMPLETE
            reason = "regular_interval"
            _append_log(evidence_dir, "\n".join(["COMMAND: " + " ".join(cmd), "STDERR:", completed.stderr or ""]))
        except subprocess.CalledProcessError as exc:
            status = STATUS_ERROR
            reason = exc.stderr[-1000:]
            _append_log(evidence_dir, "\n".join(["COMMAND: " + " ".join(cmd), "STDERR:", exc.stderr or ""]))
        records.append(
            {
                "sample_id": deterministic_id(
                    "FRM",
                    media_metadata.get("sha256"),
                    profile_hash or "",
                    f"{timestamp:.3f}",
                ),
                "timestamp": timestamp,
                "frame_index": int(math.floor(timestamp * fps)) if fps else None,
                "image_path": str(frame_path),
                "reason": reason,
                "status": status,
            }
        )

    result = {
        "sampling_status": STATUS_COMPLETE if all(item["status"] == STATUS_COMPLETE for item in records) else STATUS_LIMITED,
        "sample_interval_sec": sample_interval,
        "sample_count": len(records),
        "samples": records,
        "limitations": [
            "This is interval sampling only. Face, pose, and object analysis require optional computer vision dependencies."
        ],
    }
    if evidence_dir:
        write_json(evidence_dir / "sampling_logs.json", result)
    return result
