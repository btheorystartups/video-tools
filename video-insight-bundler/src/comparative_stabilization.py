"""Comparative stability evaluation across a local corpus."""

from __future__ import annotations

from statistics import pstdev

from intelligence_common import avg, base_artifact, clamp, deterministic_id


def _stability(values: list[float | None]) -> float:
    clean = [float(value) for value in values if value is not None]
    if len(clean) < 2:
        return 0.25
    return clamp(1.0 - min(pstdev(clean), 1.0))


def _classify(count: int, score: float) -> str:
    if count < 3:
        return "insufficient_corpus"
    if score < 0.42:
        return "unstable"
    if score < 0.6:
        return "emerging"
    if score < 0.78:
        return "stable"
    return "strong"


def build_comparative_stabilization(analyses: list[dict], comparative_outputs: dict, archetypes: dict) -> dict:
    style = comparative_outputs.get("style_fingerprint") or {}
    pacing = comparative_outputs.get("pacing_fingerprint") or {}
    discourse = comparative_outputs.get("discourse_fingerprint") or {}
    creator = comparative_outputs.get("creator_evolution") or {}
    recommendations = comparative_outputs.get("comparative_recommendations") or {}
    readiness_values = [(analysis.get("release_readiness") or {}).get("release_readiness_score") for analysis in analyses]
    style_stability = _stability([row.get("structural_rhythm_signature") for row in style.get("style_fingerprints", [])])
    pacing_stability = _stability([row.get("pacing_wave_profile") for row in pacing.get("pacing_fingerprints", [])])
    discourse_stability = _stability([row.get("discourse_pressure_signature") for row in discourse.get("discourse_fingerprints", [])])
    recommendation_stability = clamp((recommendations.get("summary") or {}).get("recurring_recommendation_count", 0) / max((recommendations.get("summary") or {}).get("unique_recommendation_family_count", 1), 1))
    archetype_stability = clamp(len(archetypes.get("archetype_counts") or {}) / max(len(analyses), 1))
    creator_stability = (creator.get("summary") or {}).get("creator_stability_score") or 0.35
    comparative_volatility = clamp(max([value or 0 for value in readiness_values], default=0) - min([value or 0 for value in readiness_values], default=0))
    score = avg([style_stability, pacing_stability, discourse_stability, recommendation_stability, archetype_stability, creator_stability, 1.0 - comparative_volatility])
    output = base_artifact(method="deterministic_comparative_stabilization_v1")
    output.update(
        {
            "comparative_stabilization_id": deterministic_id("CSTAB", len(analyses), score, comparative_volatility),
            "sufficient_video_count": len(analyses) >= 3,
            "style_fingerprint_stability": style_stability,
            "pacing_fingerprint_stability": pacing_stability,
            "discourse_fingerprint_stability": discourse_stability,
            "recurring_recommendation_stability": recommendation_stability,
            "archetype_stability": archetype_stability,
            "creator_evolution_stability": creator_stability,
            "comparative_volatility": comparative_volatility,
            "comparative_stability_score": score,
            "classification": _classify(len(analyses), score),
            "summary": {
                "analysis_count": len(analyses),
                "comparative_stability_score": score,
                "classification": _classify(len(analyses), score),
            },
        }
    )
    return output
