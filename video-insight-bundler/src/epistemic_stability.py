"""Epistemic stability analysis over local deterministic evidence."""

from __future__ import annotations

from intelligence_common import avg, base_artifact, clamp, deterministic_id, read_json


def build_epistemic_stability(bundle, recommendation_dependencies: dict, revision_forecasting: dict, counterfactual_simulation: dict) -> dict:
    root = bundle.output_dir
    consensus = getattr(bundle, "consensus_outputs", None) or {}
    longitudinal = read_json(root / "longitudinal" / "longitudinal_summary.json")
    dependency_pressure = (recommendation_dependencies.get("summary") or {}).get("recommendation_dependency_pressure") or 0.0
    forecast_uncertainty = avg([row.get("forecast_uncertainty") for row in revision_forecasting.get("revision_forecasts", [])])
    counterfactual_uncertainty = (counterfactual_simulation.get("summary") or {}).get("mean_counterfactual_uncertainty") or 0.0
    consensus_mean = (((consensus.get("evidence_consensus") or {}).get("summary") or {}).get("consensus_score_distribution") or {}).get("mean") or 0.35
    longitudinal_confidence = longitudinal.get("longitudinal_confidence")
    stability_score = clamp(float(consensus_mean) * 0.38 + (1.0 - dependency_pressure) * 0.2 + (1.0 - forecast_uncertainty) * 0.18 + (1.0 - counterfactual_uncertainty) * 0.14 + float(longitudinal_confidence or 0.35) * 0.1)
    output = base_artifact(method="deterministic_epistemic_stability_v1")
    output.update(
        {
            "epistemic_stability_id": deterministic_id("EPI", consensus_mean, dependency_pressure, forecast_uncertainty, counterfactual_uncertainty),
            "metric_stability": {
                "consensus_stability": clamp(consensus_mean),
                "recommendation_convergence": clamp(1.0 - dependency_pressure),
                "forecast_stability": clamp(1.0 - forecast_uncertainty),
                "counterfactual_stability": clamp(1.0 - counterfactual_uncertainty),
                "longitudinal_consistency": longitudinal_confidence,
            },
            "stability_score": stability_score,
            "stability_class": "stable" if stability_score >= 0.72 else "mixed" if stability_score >= 0.52 else "unstable",
            "summary": {
                "epistemic_stability_score": stability_score,
                "analysis_convergence": clamp(consensus_mean),
                "historical_interpretation_stability": longitudinal_confidence,
                "recommendation_convergence": clamp(1.0 - dependency_pressure),
            },
        }
    )
    return output
