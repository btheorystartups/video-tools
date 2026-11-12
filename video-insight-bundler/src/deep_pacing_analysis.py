"""Deep transcript-derived pacing and delivery analysis."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, pstdev

from audio_transcript_packet import count_words
from stability import utc_now_iso


def _score(value: float | None, target: float, spread: float) -> float:
    if value is None:
        return 0.0
    return round(max(0.0, 1.0 - abs(value - target) / spread), 3)


def build_deep_pacing_analysis(transcript_packet: dict, output_root: Path) -> dict:
    audio_analysis = output_root / "audio_analysis"
    audio_analysis.mkdir(parents=True, exist_ok=True)
    transcript = transcript_packet.get("transcript") or {}
    segments = transcript.get("segments") or []
    total_words = count_words(transcript.get("text", ""))
    duration = max([float(row.get("end_sec") or 0.0) for row in segments] or [0.0])
    overall_wpm = round(total_words / max(duration / 60.0, 1e-9), 2) if duration and total_words else None
    curve = []
    for row in segments:
        wpm = float(row.get("wpm") or 0.0)
        curve.append(
            {
                "segment_id": row.get("segment_id"),
                "start_sec": row.get("start_sec"),
                "end_sec": row.get("end_sec"),
                "wpm": round(wpm, 2),
                "word_count": row.get("word_count"),
                "pacing_band": "high" if wpm >= 185 else "slow" if wpm and wpm < 95 else "candidate_optimal_range",
            }
        )
    rates = [row["wpm"] for row in curve if row["word_count"]]
    volatility = round(pstdev(rates), 2) if len(rates) > 1 else 0.0
    spikes = [row for row in curve if row["wpm"] >= 185]
    slow = [row for row in curve if row["wpm"] and row["wpm"] < 95]
    dense = [row for row in curve if (row.get("word_count") or 0) >= 45 or row["wpm"] >= 175]
    pause_ops = [
        {
            "segment_id": row.get("segment_id"),
            "time_sec": row.get("end_sec"),
            "reason": "Candidate pause before/after dense or high-WPM section; review recommended.",
        }
        for row in dense[:25]
    ]
    rerecord = [
        {
            "segment_id": row.get("segment_id"),
            "reason": "High WPM may suggest a re-record candidate if clarity is affected.",
            "wpm": row["wpm"],
        }
        for row in spikes[:25]
    ]
    preserve = [
        {
            "segment_id": row.get("segment_id"),
            "reason": "Energetic cadence may be intentional; preserve if it supports the moment.",
            "wpm": row["wpm"],
        }
        for row in curve
        if 145 <= row["wpm"] < 185
    ][:25]
    metrics = {
        "generated_at_utc": utc_now_iso(),
        "analysis_status": "complete" if segments else "limited",
        "basis": "timed transcript artifacts",
        "overall_words_per_minute": overall_wpm,
        "candidate_optimal_pacing_range_wpm": [110, 165],
        "suggested_pacing_target_wpm": 140,
        "segment_wpm": curve,
        "rolling_wpm": curve,
        "sentence_wpm": [],
        "paragraph_wpm": [],
        "pacing_volatility": volatility,
        "pacing_consistency_score": _score(volatility, 20, 85),
        "cognitive_load_pacing_score": _score(mean(rates) if rates else None, 140, 100),
        "pacing_spike_locations": spikes,
        "slow_drag_sections": slow,
        "dense_explanation_sections": dense,
        "high_wpm_low_pause_sections": spikes,
        "high_rhetorical_density_high_wpm_sections": dense,
        "recommended_pause_insertion_points": pause_ops,
        "recommended_re_record_candidates": rerecord,
        "preserve_as_intentional_candidates": preserve,
        "pace_recovery_after_dense_sections": [],
        "limitations": ["Pacing is transcript-timing derived and is a candidate review signal, not an objective optimality claim."],
    }
    (audio_analysis / "deep_pacing_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    (audio_analysis / "pacing_curve.json").write_text(json.dumps(curve, indent=2, ensure_ascii=False), encoding="utf-8")
    with (audio_analysis / "pacing_curve.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["segment_id", "start_sec", "end_sec", "wpm", "word_count", "pacing_band"])
        writer.writeheader()
        writer.writerows(curve)
    (audio_analysis / "pacing_spike_registry.json").write_text(json.dumps({"pacing_spikes": spikes}, indent=2), encoding="utf-8")
    (audio_analysis / "delivery_rhythm_registry.json").write_text(json.dumps({"delivery_patterns": curve, "pacing_volatility": volatility}, indent=2), encoding="utf-8")
    (audio_analysis / "pause_opportunity_registry.json").write_text(json.dumps({"pause_opportunities": pause_ops}, indent=2), encoding="utf-8")
    (audio_analysis / "cognitive_load_pacing_registry.json").write_text(json.dumps({"dense_sections": dense, "cognitive_load_pacing_score": metrics["cognitive_load_pacing_score"]}, indent=2), encoding="utf-8")
    lines = [
        "# Optimal Pacing Recommendations",
        "",
        "These are candidate review points, not objectively optimal conclusions.",
        "",
        f"- Overall WPM: `{overall_wpm}`",
        "- Candidate optimal pacing range: `110-165 WPM`",
        "- Suggested pacing target: `140 WPM`",
        "- Add pauses before dense concepts where listed in `pause_opportunity_registry.json`.",
        "- Slow down high-WPM sections if clarity is affected.",
        "- Preserve energetic cadence when intentional and understandable.",
        "- Add a visual reset if pacing density remains high after script review.",
    ]
    (audio_analysis / "optimal_pacing_recommendations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metrics
