"""Conservative revision forecasting from propagation and counterfactual estimates."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


def build_revision_forecasting(bundle, revision_propagation: dict, counterfactual_simulation: dict) -> dict:
    propagation_rows = revision_propagation.get("propagation_estimates") or []
    scenario_rows = counterfactual_simulation.get("counterfactual_scenarios") or []
    rows = []
    for prop in propagation_rows:
        impact = (prop.get("estimated_effects") or {}).get("readiness_impact_estimate") or 0.0
        uncertainty = prop.get("propagation_uncertainty") or 0.0
        rows.append(
            {
                "forecast_id": deterministic_id("FORE", prop.get("propagation_id"), impact, uncertainty),
                "source_propagation_id": prop.get("propagation_id"),
                "forecast_class": "low_risk_review" if uncertainty < 0.35 else "uncertain_review" if uncertainty < 0.58 else "high_uncertainty_review",
                "expected_readiness_shift": clamp(impact * (1.0 - uncertainty * 0.5)),
                "forecast_uncertainty": clamp(uncertainty),
                "heatmap_bucket": "high" if impact >= 0.04 else "medium" if impact >= 0.02 else "low",
            }
        )
    output = base_artifact(method="deterministic_revision_forecasting_v1")
    output.update(
        {
            "revision_forecasts": rows,
            "scenario_forecasts": [
                {
                    "scenario_forecast_id": deterministic_id("SFORE", row.get("counterfactual_id")),
                    "counterfactual_id": row.get("counterfactual_id"),
                    "expected_readiness_shift": (row.get("estimated_shifts") or {}).get("readiness_shift"),
                    "forecast_uncertainty": row.get("counterfactual_uncertainty"),
                }
                for row in scenario_rows
            ],
            "summary": {
                "forecast_count": len(rows),
                "high_uncertainty_forecast_count": sum(1 for row in rows if row["forecast_class"] == "high_uncertainty_review"),
                "mean_expected_readiness_shift": clamp(sum(row["expected_readiness_shift"] for row in rows) / max(len(rows), 1)),
            },
        }
    )
    return output
