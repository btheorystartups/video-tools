"""Pause, silence, acoustic energy, loudness proxy, and dynamic range exports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median

from stability import utc_now_iso


def _load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default


def build_pause_silence_and_acoustic_outputs(analysis_root: Path, output_root: Path, transcript_packet: dict) -> dict:
    audio_analysis = output_root / "audio_analysis"
    audio_analysis.mkdir(parents=True, exist_ok=True)
    acoustic = _load_json(analysis_root / "acoustic_features.json", {})
    if not acoustic and (analysis_root / "corpus" / "corpus_run_manifest.json").exists():
        manifest = _load_json(analysis_root / "corpus" / "corpus_run_manifest.json", {})
        for item in manifest.get("per_video_output_dirs") or []:
            acoustic = _load_json(Path(item) / "acoustic_features.json", {})
            if acoustic:
                break
    transcript_segments = (transcript_packet.get("transcript") or {}).get("segments") or []
    pauses = []
    previous = None
    for row in transcript_segments:
        start = float(row.get("start_sec") or 0.0)
        if previous is not None and start > previous:
            duration = round(start - previous, 3)
            if duration >= 0.25:
                pauses.append({"start_sec": round(previous, 3), "end_sec": round(start, 3), "duration_sec": duration})
        previous = float(row.get("end_sec") or start)
    silent_regions = acoustic.get("estimated_silent_regions") or []
    durations = [float(row.get("duration_sec") or (float(row.get("end_sec", 0)) - float(row.get("start_sec", 0)))) for row in pauses]
    pause_metrics = {
        "generated_at_utc": utc_now_iso(),
        "analysis_status": "complete" if pauses or silent_regions else "limited",
        "silence_ratio": acoustic.get("silence_ratio"),
        "pause_count": len(pauses),
        "pause_duration_distribution": {
            "min": round(min(durations), 3) if durations else None,
            "max": round(max(durations), 3) if durations else None,
            "median": round(median(durations), 3) if durations else None,
        },
        "median_pause_length": round(median(durations), 3) if durations else None,
        "long_pauses": [row for row in pauses if row["duration_sec"] >= 1.5],
        "missing_pause_candidates": [],
        "pause_density": round(len(pauses) / max((transcript_segments[-1].get("end_sec") if transcript_segments else 60) / 60.0, 1e-9), 3),
        "pause_alignment_with_transcript_boundaries": "derived_from_segment_gaps" if pauses else "limited",
        "pause_alignment_with_rhetorical_transitions": "review_recommended",
        "limitations": ["Silence is not uncertainty; human review is required."],
    }
    energy_curve = acoustic.get("rms_energy_over_time") or []
    energy_values = [float(row.get("rms") or 0.0) for row in energy_curve]
    energy_metrics = {
        "generated_at_utc": utc_now_iso(),
        "analysis_status": acoustic.get("analysis_status", "limited"),
        "rms_energy": acoustic.get("rms_energy_summary"),
        "energy_variance": acoustic.get("energy_variability"),
        "energy_spikes": sorted(energy_curve, key=lambda row: float(row.get("rms") or 0.0), reverse=True)[:25],
        "low_energy_stretches": acoustic.get("estimated_silent_regions") or [],
        "dynamic_range_proxy": round(max(energy_values) - min(energy_values), 6) if energy_values else None,
        "clipping_risk_proxy": "review" if energy_values and max(energy_values) >= 0.98 else "not_flagged",
        "noise_floor_proxy": acoustic.get("silence_threshold_rms"),
        "emphasis_candidates": sorted(energy_curve, key=lambda row: float(row.get("rms") or 0.0), reverse=True)[:10],
        "abrupt_acoustic_transitions": acoustic.get("acoustic_contrast_between_segments") or [],
        "limitations": ["Acoustic energy is not emotion; loudness is not confidence."],
    }
    loudness = {"generated_at_utc": utc_now_iso(), "analysis_status": energy_metrics["analysis_status"], "loudness_proxy": acoustic.get("rms_energy_summary"), "limitations": ["Loudness proxy is not confidence."]}
    dynamic = {"generated_at_utc": utc_now_iso(), "analysis_status": energy_metrics["analysis_status"], "dynamic_range_proxy": energy_metrics["dynamic_range_proxy"], "limitations": ["Dynamic range is an acoustic proxy only."]}
    quality = {"generated_at_utc": utc_now_iso(), "flags": [flag for flag in [energy_metrics["clipping_risk_proxy"] if energy_metrics["clipping_risk_proxy"] != "not_flagged" else None] if flag], "human_review_required": True}
    (audio_analysis / "pause_silence_metrics.json").write_text(json.dumps(pause_metrics, indent=2), encoding="utf-8")
    (audio_analysis / "silence_segments.json").write_text(json.dumps(silent_regions or pauses, indent=2), encoding="utf-8")
    with (audio_analysis / "silence_segments.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["start_sec", "end_sec", "duration_sec"])
        writer.writeheader()
        writer.writerows(silent_regions or pauses)
    (audio_analysis / "acoustic_energy_metrics.json").write_text(json.dumps(energy_metrics, indent=2), encoding="utf-8")
    (audio_analysis / "acoustic_energy_curve.json").write_text(json.dumps(energy_curve, indent=2), encoding="utf-8")
    with (audio_analysis / "acoustic_energy_curve.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time_sec", "rms"])
        writer.writeheader()
        writer.writerows(energy_curve)
    (audio_analysis / "loudness_proxy_metrics.json").write_text(json.dumps(loudness, indent=2), encoding="utf-8")
    (audio_analysis / "dynamic_range_metrics.json").write_text(json.dumps(dynamic, indent=2), encoding="utf-8")
    (audio_analysis / "audio_quality_flags.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    return {"pause_silence_metrics": pause_metrics, "acoustic_energy_metrics": energy_metrics, "loudness_proxy_metrics": loudness, "dynamic_range_metrics": dynamic, "audio_quality_flags": quality}
