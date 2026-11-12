"""Benchmark-aware deterministic comparisons for expert review dashboards."""

from __future__ import annotations

from statistics import median

from intelligence_common import base_artifact, num
from stability import deterministic_id


def _percentile(value: float, values: list[float]) -> float:
    clean = sorted(num(item) for item in values if item is not None)
    if not clean:
        return 0.0
    below = sum(1 for item in clean if item <= value)
    return round(below / len(clean), 3)


def _classify(value: float, values: list[float], higher_is_better: bool) -> str:
    if not values:
        return "insufficient_benchmark"
    pct = _percentile(value, values)
    if higher_is_better:
        if pct >= 0.75:
            return "above_corpus_median"
        if pct <= 0.25:
            return "below_corpus_median"
    else:
        if pct >= 0.75:
            return "elevated_against_corpus"
        if pct <= 0.25:
            return "low_against_corpus"
    return "near_corpus_median"


def build_benchmark_comparison_registry(outputs: dict) -> dict:
    videos = (outputs.get("corpus_index") or {}).get("videos") or []
    specs = [
        ("readiness_score", "Readiness Score", "readiness_score", True),
        ("peak_pressure_score", "Peak Pressure", "peak_pressure_score", False),
        ("structural_coherence_score", "Structural Coherence", "structural_coherence_score", True),
        ("warning_count", "Warning Count", "warning_count", False),
    ]
    rows = []
    for metric_id, label, source_key, higher_is_better in specs:
        values = [row.get(source_key) for row in videos if row.get(source_key) is not None]
        med = round(median([num(v) for v in values]), 3) if values else None
        for video in videos:
            if video.get(source_key) is None:
                continue
            value = num(video.get(source_key))
            rows.append(
                {
                    "benchmark_id": deterministic_id("BENCH", metric_id, video.get("corpus_item_id"), value),
                    "metric_id": metric_id,
                    "display_name": label,
                    "scope": "video_to_corpus",
                    "source_video": video.get("source_video"),
                    "source_corpus_item_id": video.get("corpus_item_id"),
                    "current_value": round(value, 3),
                    "corpus_median": med,
                    "percentile_position": _percentile(value, values),
                    "balanced_elevated_extreme_classification": _classify(value, values, higher_is_better),
                    "directional_interpretation": "Higher values are usually favorable for this local benchmark." if higher_is_better else "Lower values usually reduce review burden for this local benchmark.",
                    "uncertainty_notes": [
                        "Corpus medians are local to the analyzed corpus and are not universal quality standards.",
                        "Small corpora can make percentile positions coarse.",
                    ],
                    "evidence_refs": ["corpus/corpus_index.json"],
                }
            )
    output = base_artifact(method="deterministic_benchmark_comparison_v1")
    output.update(
        {
            "benchmark_comparison_registry_id": deterministic_id("BREG", [(row["metric_id"], row["source_corpus_item_id"], row["current_value"]) for row in rows]),
            "benchmark_comparisons": rows,
            "summary": {"benchmark_comparison_count": len(rows), "video_count": len(videos)},
        }
    )
    return output
