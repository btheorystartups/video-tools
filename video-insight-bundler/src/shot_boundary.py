"""Deterministic local shot-boundary evidence from sampled video frames."""

from __future__ import annotations

import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from stability import STATUS_COMPLETE, STATUS_LIMITED, STATUS_UNAVAILABLE, deterministic_id, write_json

try:  # pragma: no cover - dependency availability varies by machine
    import cv2
    import numpy as np
except Exception:  # pragma: no cover
    cv2 = None
    np = None


MODE_INTERVALS = {"coarse": 5.0, "normal": 2.0, "dense": 0.75}
MODE_THRESHOLDS = {"coarse": 0.52, "normal": 0.46, "dense": 0.42}
DEFAULT_THRESHOLD = MODE_THRESHOLDS["normal"]
DEFAULT_SCORE_WEIGHTS = {
    "histogram_difference": 0.3,
    "mean_absolute_pixel_difference": 0.32,
    "edge_difference": 0.18,
    "brightness_contrast_change": 0.2,
}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 3)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _distribution(values: list[float]) -> dict:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None, "stddev": None}
    return {
        "count": len(clean),
        "min": round(min(clean), 3),
        "max": round(max(clean), 3),
        "mean": round(mean(clean), 3),
        "stddev": round(pstdev(clean), 3) if len(clean) > 1 else 0.0,
    }


def _placeholder(reason: str, mode: str, interval: float, threshold: float) -> dict:
    return {
        "analysis_status": STATUS_UNAVAILABLE,
        "method": "opencv_unavailable_placeholder",
        "sampling_rate": {"mode": mode, "sample_interval_sec": interval, "sample_count": 0},
        "detected_boundaries": [],
        "boundary_confidence": {"count": 0, "mean": None, "max": None},
        "visual_change_score": {"count": 0, "min": None, "max": None, "mean": None, "stddev": None},
        "threshold_used": threshold,
        "neighboring_frame_paths": [],
        "sampled_frame_features": [],
        "limitations": [
            reason,
            "OpenCV is optional; downstream visual artifacts are placeholders when it is unavailable.",
            "No cinematic intent, identity, face, emotion, object, or semantic claims are made.",
        ],
    }


def _timestamps(duration: float, interval: float, max_samples: int) -> list[float]:
    if duration <= 0:
        return [0.0]
    points: list[float] = []
    current = 0.0
    while current <= duration and len(points) < max_samples:
        points.append(round(current, 3))
        current += max(interval, 0.1)
    if points and points[-1] < duration - 0.5 and len(points) < max_samples:
        points.append(round(duration - 0.1, 3))
    return points


def _score_weights(visual_profile: dict) -> dict:
    configured = visual_profile.get("shot_boundary_score_weights") or {}
    weights = {
        name: _num(configured.get(name), default)
        for name, default in DEFAULT_SCORE_WEIGHTS.items()
    }
    total = sum(max(value, 0.0) for value in weights.values())
    if total <= 0:
        return DEFAULT_SCORE_WEIGHTS.copy()
    return {name: value / total for name, value in weights.items()}


def _frame_metrics(frame, previous, weights: dict) -> dict:
    resized = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(gray, 80, 160)
    brightness = float(gray.mean()) / 255.0
    contrast = float(gray.std()) / 128.0
    saturation = float(hsv[:, :, 1].mean()) / 255.0
    edge_density = float((edges > 0).mean())
    histogram = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(histogram, histogram)
    current = {
        "small_frame": resized,
        "gray": gray,
        "edges": edges,
        "histogram": histogram,
        "brightness": _clamp(brightness),
        "contrast": _clamp(contrast),
        "saturation_proxy": _clamp(saturation),
        "edge_density": _clamp(edge_density),
        "visual_complexity": _clamp(edge_density * 0.46 + min(contrast, 1.0) * 0.34 + saturation * 0.2),
    }
    if previous is None:
        current.update(
            {
                "histogram_difference": 0.0,
                "mean_absolute_pixel_difference": 0.0,
                "edge_difference": 0.0,
                "brightness_change": 0.0,
                "contrast_change": 0.0,
                "combined_change_score": 0.0,
            }
        )
        return current
    hist_diff = float(cv2.compareHist(previous["histogram"], histogram, cv2.HISTCMP_BHATTACHARYYA))
    pixel_diff = float(np.mean(np.abs(resized.astype("float32") - previous["small_frame"].astype("float32"))) / 255.0)
    edge_diff = float(np.mean(np.abs(edges.astype("float32") - previous["edges"].astype("float32"))) / 255.0)
    brightness_change = abs(current["brightness"] - previous["brightness"])
    contrast_change = abs(current["contrast"] - previous["contrast"])
    combined = (
        hist_diff * weights["histogram_difference"]
        + pixel_diff * weights["mean_absolute_pixel_difference"]
        + edge_diff * weights["edge_difference"]
        + min(brightness_change + contrast_change, 1.0) * weights["brightness_contrast_change"]
    )
    current.update(
        {
            "histogram_difference": _clamp(hist_diff),
            "mean_absolute_pixel_difference": _clamp(pixel_diff),
            "edge_difference": _clamp(edge_diff),
            "brightness_change": _clamp(brightness_change),
            "contrast_change": _clamp(contrast_change),
            "combined_change_score": _clamp(combined),
        }
    )
    return current


def _save_neighbor(path: Path, frame) -> str | None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), frame)
        return path.as_posix()
    except Exception:
        return None


def detect_shot_boundaries(
    video_path: Path,
    output_dir: Path,
    media_metadata: dict,
    profile: dict | None = None,
    evidence_dir: Path | None = None,
) -> dict:
    """Sample frames and produce deterministic shot/visual-transition evidence."""

    profile = profile or {}
    visual_profile = profile.get("visual_structure") or {}
    mode = str(visual_profile.get("shot_sampling_mode") or "normal").lower()
    if mode not in MODE_INTERVALS:
        mode = "normal"
    interval = float(visual_profile.get("shot_sample_interval_sec") or MODE_INTERVALS[mode])
    configured_mode_thresholds = visual_profile.get("shot_boundary_mode_thresholds") or {}
    mode_threshold = _num(configured_mode_thresholds.get(mode), MODE_THRESHOLDS[mode])
    threshold = float(visual_profile.get("shot_boundary_threshold") or mode_threshold)
    weights = _score_weights(visual_profile)
    max_samples = int(visual_profile.get("max_shot_samples") or 900)

    if cv2 is None or np is None:
        result = _placeholder("OpenCV is unavailable; visual shot-boundary detection was not run.", mode, interval, threshold)
        if evidence_dir:
            write_json(evidence_dir / "shot_boundary_sampling_log.json", result)
        return result
    if not video_path.exists():
        result = _placeholder(f"Video file is unavailable: {video_path}", mode, interval, threshold)
        if evidence_dir:
            write_json(evidence_dir / "shot_boundary_sampling_log.json", result)
        return result

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        result = _placeholder("OpenCV could not open the source video.", mode, interval, threshold)
        if evidence_dir:
            write_json(evidence_dir / "shot_boundary_sampling_log.json", result)
        return result

    fps = _num(media_metadata.get("fps"), capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    detected_duration = frame_count / fps if fps > 0 and frame_count else 0.0
    duration = _num(media_metadata.get("duration_sec"), detected_duration)
    timestamps = _timestamps(duration, interval, max_samples)
    sha = media_metadata.get("sha256")
    samples: list[dict] = []
    boundaries: list[dict] = []
    neighbors: list[str] = []
    previous_metrics = None
    previous_frame = None
    previous_timestamp = None

    for index, timestamp in enumerate(timestamps):
        capture.set(cv2.CAP_PROP_POS_MSEC, max(timestamp, 0.0) * 1000.0)
        ok, frame = capture.read()
        if not ok or frame is None:
            continue
        metrics = _frame_metrics(frame, previous_metrics, weights)
        sample = {
            "sample_id": deterministic_id("VFRM", sha, mode, f"{timestamp:.3f}"),
            "timestamp_sec": round(timestamp, 3),
            "frame_index": int(round(timestamp * fps)) if fps else None,
            "brightness": metrics["brightness"],
            "contrast": metrics["contrast"],
            "saturation_proxy": metrics["saturation_proxy"],
            "edge_density": metrics["edge_density"],
            "visual_complexity": metrics["visual_complexity"],
            "histogram_difference": metrics["histogram_difference"],
            "mean_absolute_pixel_difference": metrics["mean_absolute_pixel_difference"],
            "edge_difference": metrics["edge_difference"],
            "brightness_change": metrics["brightness_change"],
            "contrast_change": metrics["contrast_change"],
            "visual_change_score": metrics["combined_change_score"],
            "frame_similarity_to_previous": _clamp(1.0 - metrics["combined_change_score"]),
        }
        samples.append(sample)
        if previous_metrics is not None and metrics["combined_change_score"] >= threshold:
            boundary_id = deterministic_id("SHOT", sha, f"{previous_timestamp:.3f}", f"{timestamp:.3f}", f"{threshold:.3f}")
            before_path = _save_neighbor(output_dir / "visual_structure" / "neighbor_frames" / f"{boundary_id}_before.jpg", previous_frame)
            after_path = _save_neighbor(output_dir / "visual_structure" / "neighbor_frames" / f"{boundary_id}_after.jpg", frame)
            paths = [item for item in [before_path, after_path] if item]
            neighbors.extend(paths)
            confidence = _clamp(0.45 + ((metrics["combined_change_score"] - threshold) / max(1.0 - threshold, 0.001)) * 0.55)
            boundaries.append(
                {
                    "boundary_id": boundary_id,
                    "boundary_index": len(boundaries) + 1,
                    "timestamp_sec": round(timestamp, 3),
                    "previous_timestamp_sec": round(float(previous_timestamp or 0.0), 3),
                    "boundary_confidence": confidence,
                    "visual_change_score": metrics["combined_change_score"],
                    "threshold_used": threshold,
                    "method_scores": {
                        "histogram_difference": metrics["histogram_difference"],
                        "mean_absolute_pixel_difference": metrics["mean_absolute_pixel_difference"],
                        "edge_difference": metrics["edge_difference"],
                        "brightness_change": metrics["brightness_change"],
                        "contrast_change": metrics["contrast_change"],
                    },
                    "neighboring_frame_paths": paths,
                    "interpretation": "local_pixel_level_visual_transition_candidate",
                    "limitations": [
                        "This boundary is a deterministic visual-change candidate, not a claim about cinematic intent.",
                        "No object, face, identity, or emotion recognition was used.",
                    ],
                }
            )
        previous_metrics = metrics
        previous_frame = frame.copy()
        previous_timestamp = timestamp

    capture.release()
    change_scores = [row["visual_change_score"] for row in samples[1:]]
    confidences = [row["boundary_confidence"] for row in boundaries]
    result = {
        "analysis_status": STATUS_COMPLETE if samples else STATUS_LIMITED,
        "method": "opencv_histogram_pixel_edge_change_v1",
        "sampling_rate": {
            "mode": mode,
            "sample_interval_sec": interval,
            "sample_count": len(samples),
            "fps_observed": round(fps, 3) if fps else None,
        },
        "detected_boundaries": boundaries,
        "boundary_confidence": {
            "count": len(confidences),
            "mean": round(mean(confidences), 3) if confidences else None,
            "max": round(max(confidences), 3) if confidences else None,
        },
        "visual_change_score": _distribution(change_scores),
        "threshold_used": threshold,
        "threshold_profile": {
            "mode_thresholds": MODE_THRESHOLDS,
            "score_weights": {name: round(value, 3) for name, value in weights.items()},
            "calibration": "conservative_pixel_color_edge_v2",
        },
        "neighboring_frame_paths": neighbors,
        "sampled_frame_features": samples,
        "limitations": [
            "Shot boundaries are deterministic pixel/color/edge-level evidence summaries for editorial review.",
            "They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.",
            "Sampling interval may miss very short visual transitions between samples.",
        ],
    }
    if evidence_dir:
        write_json(
            evidence_dir / "shot_boundary_sampling_log.json",
            {
                "analysis_status": result["analysis_status"],
                "method": result["method"],
                "sampling_rate": result["sampling_rate"],
                "threshold_used": threshold,
                "sampled_timestamp_count": len(timestamps),
                "read_sample_count": len(samples),
                "detected_boundary_count": len(boundaries),
                "limitations": result["limitations"],
            },
        )
    return result
