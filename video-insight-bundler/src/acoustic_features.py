"""Local acoustic energy and rhythm analysis."""

from __future__ import annotations

import math
from statistics import mean, pstdev
from pathlib import Path

from stability import STATUS_COMPLETE, STATUS_UNAVAILABLE


def _distribution(values: list[float]) -> dict:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "stddev": None}
    ordered = sorted(clean)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    return {
        "count": len(clean),
        "min": round(min(clean), 6),
        "max": round(max(clean), 6),
        "mean": round(mean(clean), 6),
        "median": round(median, 6),
        "stddev": round(pstdev(clean), 6) if len(clean) > 1 else 0.0,
    }


def _region_records(times: list[float], flags: list[bool], target: bool) -> list[dict]:
    regions: list[dict] = []
    start = None
    previous = None
    for time_sec, flag in zip(times, flags):
        if flag == target and start is None:
            start = time_sec
        if flag != target and start is not None:
            regions.append({"start_sec": round(start, 3), "end_sec": round(previous or start, 3)})
            start = None
        previous = time_sec
    if start is not None:
        regions.append({"start_sec": round(start, 3), "end_sec": round(previous or start, 3)})
    return regions


def _segment_energy(segments: list[dict], times: list[float], rms: list[float]) -> list[dict]:
    output = []
    for segment in segments:
        start = float(segment.get("start_sec") or 0.0)
        end = float(segment.get("end_sec") or start)
        values = [value for time_sec, value in zip(times, rms) if start <= time_sec <= end]
        dist = _distribution(values)
        output.append(
            {
                "segment_id": segment.get("segment_id"),
                "start_sec": round(start, 3),
                "end_sec": round(end, 3),
                "average_energy": dist["mean"],
                "energy_variability": dist["stddev"],
                "sample_count": dist["count"],
            }
        )
    return output


def _trend(values: list[float]) -> dict:
    if len(values) < 2:
        return {"direction": "insufficient_data", "slope": None}
    first = mean(values[: max(1, len(values) // 5)])
    last = mean(values[-max(1, len(values) // 5):])
    delta = last - first
    if abs(delta) < max(max(values), 1e-9) * 0.04:
        direction = "mostly_flat"
    elif delta > 0:
        direction = "rising"
    else:
        direction = "falling"
    return {"direction": direction, "first_window_mean": round(first, 6), "last_window_mean": round(last, 6), "delta": round(delta, 6)}


def analyze_acoustic_features(audio_result: dict, scene_segments: dict, media_metadata: dict) -> dict:
    audio_path = audio_result.get("audio_path")
    if not audio_path or not Path(audio_path).exists():
        return {
            "analysis_status": STATUS_UNAVAILABLE,
            "basis": "local audio waveform",
            "reason": "No extracted local audio file was available for acoustic analysis.",
            "segments": [],
            "limitations": [
                "Acoustic features require a local extracted audio file.",
                "These outputs describe energy and rhythm evidence only, not emotion or intent.",
            ],
        }

    try:
        import librosa
        import numpy as np
    except Exception as exc:  # pragma: no cover - depends on optional environment
        return {
            "analysis_status": STATUS_UNAVAILABLE,
            "basis": "local audio waveform",
            "reason": f"librosa or numpy unavailable: {exc}",
            "segments": [],
            "limitations": [
                "Install librosa and numpy to enable acoustic waveform analysis.",
                "These outputs describe energy and rhythm evidence only, not emotion or intent.",
            ],
        }

    try:
        y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
        if y.size == 0:
            raise ValueError("audio waveform is empty")
        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
        times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    except Exception as exc:
        return {
            "analysis_status": "error",
            "basis": "local audio waveform",
            "reason": f"Acoustic analysis failed: {exc}",
            "segments": [],
            "limitations": [
                "Acoustic analysis could not read the local audio waveform.",
                "These outputs describe energy and rhythm evidence only, not emotion or intent.",
            ],
        }

    rms_values = [float(value) for value in rms]
    time_values = [float(value) for value in times]
    if not rms_values:
        threshold = 0.0
    else:
        threshold = max(float(np.percentile(rms, 20)), float(np.max(rms)) * 0.035)
    silent_flags = [value <= threshold for value in rms_values]
    silence_ratio = round(sum(1 for flag in silent_flags if flag) / max(len(silent_flags), 1), 6)
    segments = _segment_energy(scene_segments.get("segments") or [], time_values, rms_values)
    contrasts = []
    for left, right in zip(segments, segments[1:]):
        if left.get("average_energy") is None or right.get("average_energy") is None:
            contrast = None
        else:
            contrast = round(abs(float(right["average_energy"]) - float(left["average_energy"])), 6)
        contrasts.append(
            {
                "from_segment_id": left.get("segment_id"),
                "to_segment_id": right.get("segment_id"),
                "energy_contrast": contrast,
            }
        )

    voiced_regions = _region_records(time_values, silent_flags, False)
    silent_regions = _region_records(time_values, silent_flags, True)
    rhythm_proxy = None
    if len(voiced_regions) > 1:
        starts = [region["start_sec"] for region in voiced_regions]
        intervals = [right - left for left, right in zip(starts, starts[1:]) if right > left]
        if intervals:
            rhythm_proxy = {
                "voiced_region_onsets_per_minute": round(len(starts) / max((time_values[-1] or 1.0) / 60.0, 1e-9), 3),
                "onset_interval_distribution": _distribution(intervals),
            }

    return {
        "analysis_status": STATUS_COMPLETE,
        "basis": "local audio waveform via librosa",
        "sample_rate_hz": int(sr),
        "duration_sec": round(float(librosa.get_duration(y=y, sr=sr)), 3),
        "rms_energy_over_time": [
            {"time_sec": round(time_sec, 3), "rms": round(value, 6)}
            for time_sec, value in zip(time_values, rms_values)
        ],
        "rms_energy_summary": _distribution(rms_values),
        "segments": segments,
        "energy_variability": _distribution([item.get("energy_variability") for item in segments]),
        "silence_threshold_rms": round(float(threshold), 6),
        "silence_ratio": silence_ratio,
        "estimated_voiced_regions": voiced_regions[:200],
        "estimated_silent_regions": silent_regions[:200],
        "tempo_like_speaking_rhythm_proxy": rhythm_proxy,
        "spectral_centroid_summary": _distribution([float(value) for value in centroid]),
        "zero_crossing_rate_summary": _distribution([float(value) for value in zcr]),
        "acoustic_contrast_between_segments": contrasts,
        "loudness_energy_trend": _trend(rms_values),
        "limitations": [
            "Acoustic energy is not emotion detection.",
            "Voiced and silent regions are approximate RMS-threshold regions, not phoneme-level speech activity.",
            "Rhythm proxy is derived from local energy onsets and should be reviewed with transcript timing.",
        ],
    }
