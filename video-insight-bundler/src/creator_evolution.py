"""Creator-level editorial evolution from multiple local analysis folders."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, clamp, deterministic_id


def _classify(values: list[float]) -> str:
    clean = [float(value) for value in values if value is not None]
    if len(clean) < 2:
        return "inconclusive"
    delta = clean[-1] - clean[0]
    spread = max(clean) - min(clean)
    if spread >= 0.32:
        return "volatile"
    if delta >= 0.08:
        return "evolving"
    if delta <= -0.08:
        return "diverging"
    if spread <= 0.08:
        return "stabilizing"
    return "converging"


def build_creator_evolution(analyses: list[dict], style: dict, rhetorical: dict, pacing: dict, discourse: dict) -> dict:
    style_rows = style.get("style_fingerprints") or []
    disc_rows = discourse.get("discourse_fingerprints") or []
    pace_rows = pacing.get("pacing_fingerprints") or []
    continuity = [row.get("continuity_signature") for row in style_rows]
    pacing_values = [row.get("pacing_wave_profile") for row in pace_rows]
    discourse_values = [row.get("discourse_pressure_signature") for row in disc_rows]
    readiness = [(analysis.get("release_readiness") or {}).get("release_readiness_score") for analysis in analyses]
    clean_readiness = [float(value) for value in readiness if value is not None]
    rows = []
    for index, analysis in enumerate(analyses):
        rows.append(
            {
                "evolution_point_id": deterministic_id("CREVO", analysis.get("analysis_dir"), index),
                "analysis_dir": analysis.get("analysis_dir"),
                "sequence_index": index + 1,
                "continuity_score": continuity[index] if index < len(continuity) else None,
                "pacing_score": pacing_values[index] if index < len(pacing_values) else None,
                "discourse_pressure": discourse_values[index] if index < len(discourse_values) else None,
                "readiness_score": readiness[index] if index < len(readiness) else None,
            }
        )
    output = base_artifact(method="deterministic_creator_editorial_evolution_v1")
    output.update(
        {
            "creator_evolution_id": deterministic_id("CREATOR", [row.get("evolution_point_id") for row in rows]),
            "evolution_points": rows,
            "classification": _classify(clean_readiness or [avg(continuity)]),
            "dimension_classifications": {
                "continuity_evolution": _classify(continuity),
                "pacing_evolution": _classify(pacing_values),
                "discourse_evolution": _classify([1.0 - float(value) for value in discourse_values if value is not None]),
                "pressure_evolution": _classify([1.0 - float(value) for value in discourse_values if value is not None]),
                "volatility_evolution": _classify([clamp(abs(float(value) - avg(pacing_values))) for value in pacing_values if value is not None]),
            },
            "summary": {"analysis_count": len(analyses), "creator_stability_score": clamp(1.0 - max(clean_readiness or [0.0]) + min(clean_readiness or [0.0])) if len(clean_readiness) >= 2 else 0.35},
        }
    )
    return output
