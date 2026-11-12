"""Corpus-level recurring editorial intelligence."""

from __future__ import annotations

from collections import Counter

from intelligence_common import avg, base_artifact, clamp, deterministic_id


def build_corpus_intelligence(analyses: list[dict]) -> dict:
    recommendation_counts: Counter = Counter()
    phase_counts: Counter = Counter()
    weak: Counter = Counter()
    strengths: Counter = Counter()
    blockers: Counter = Counter()
    visual_patterns: Counter = Counter()
    pacing_patterns: Counter = Counter()
    discourse_patterns: Counter = Counter()
    pressure_values = []
    for analysis in analyses:
        readiness = analysis.get("release_readiness") or {}
        recs = (analysis.get("recommendations") or {}).get("recommendations") or []
        recommendation_counts.update(row.get("issue_type") for row in recs if row.get("issue_type"))
        phases = ((analysis.get("narrative_phase_model") or {}).get("summary") or {}).get("phase_counts") or {}
        phase_counts.update(phases)
        pressure = ((analysis.get("editorial_pressure") or {}).get("summary") or {}).get("peak_cumulative_pressure_score")
        if pressure is not None:
            pressure_values.append(pressure)
        for item in readiness.get("weakest_evidence") or []:
            weak[item.get("metric")] += 1
        for item in readiness.get("strongest_evidence") or []:
            strengths[item.get("metric")] += 1
        for item in readiness.get("blocking_issues") or []:
            blockers[item] += 1
        visual = analysis.get("visual_structure") or {}
        if (visual.get("visual_continuity_score") or 0) < 0.55:
            visual_patterns["low_visual_continuity"] += 1
        temporal = analysis.get("temporal_rhythm") or {}
        pacing_patterns["density_spike"] += int((temporal.get("summary") or {}).get("density_spike_count") or 0)
        discourse = analysis.get("discourse_state") or {}
        if (discourse.get("discourse_pressure_score") or 0) >= 0.35:
            discourse_patterns["high_discourse_pressure"] += 1
    output = base_artifact(method="deterministic_corpus_intelligence_v1")
    output.update(
        {
            "corpus_intelligence_id": deterministic_id("CINT", sorted(recommendation_counts.items()), len(analyses)),
            "recurring_strengths": [{"metric": key, "count": value} for key, value in strengths.most_common()],
            "recurring_weaknesses": [{"metric": key, "count": value} for key, value in weak.most_common()],
            "recurring_pressure_patterns": [{"pattern": "peak_pressure", "mean": avg(pressure_values), "high_count": sum(1 for value in pressure_values if value >= 0.7)}],
            "recurring_discourse_structures": [{"pattern": key, "count": value} for key, value in discourse_patterns.most_common()],
            "recurring_recommendation_types": [{"issue_type": key, "count": value} for key, value in recommendation_counts.most_common()],
            "recurring_visual_patterns": [{"pattern": key, "count": value} for key, value in visual_patterns.most_common()],
            "recurring_pacing_patterns": [{"pattern": key, "count": value} for key, value in pacing_patterns.most_common()],
            "recurring_readiness_blockers": [{"blocker": key, "count": value} for key, value in blockers.most_common()],
            "corpus_level_confidence": clamp(min(len(analyses) / 5.0, 1.0) * 0.55 + (1.0 - avg(pressure_values)) * 0.45 if analyses else 0.0),
            "summary": {
                "analysis_count": len(analyses),
                "recurring_recommendation_type_count": len(recommendation_counts),
                "mean_peak_pressure": avg(pressure_values),
                "readiness_blocker_count": len(blockers),
            },
        }
    )
    return output
