"""Counterfactual editorial simulation without applying edits."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


SCENARIOS = [
    ("bridge_inserted", {"continuity": 0.08, "readiness": 0.03, "volatility": -0.02, "discourse": 0.02}),
    ("pacing_normalized", {"temporal": 0.09, "readiness": 0.025, "volatility": -0.04}),
    ("callback_resolved", {"discourse": 0.08, "readiness": 0.025, "continuity": 0.03}),
    ("visual_reset_added", {"continuity": 0.035, "temporal": 0.02, "readiness": 0.015}),
    ("contradiction_reduced", {"continuity": 0.05, "discourse": 0.05, "readiness": 0.035, "volatility": -0.03}),
]


def build_counterfactual_simulation(bundle, revision_propagation: dict, editorial_pressure: dict | None = None) -> dict:
    propagation = revision_propagation.get("summary") or {}
    uncertainty = float(propagation.get("mean_propagation_uncertainty") or 0.35)
    pressure = float(((editorial_pressure or {}).get("summary") or {}).get("peak_cumulative_pressure_score") or 0.0)
    rows = []
    for scenario, deltas in SCENARIOS:
        readiness = clamp(deltas.get("readiness", 0.0) * (1.0 - uncertainty * 0.45))
        rows.append(
            {
                "counterfactual_id": deterministic_id("CF", scenario, deltas, pressure),
                "scenario": scenario,
                "simulation_status": "hypothetical_review_only",
                "estimated_shifts": {
                    "readiness_shift": readiness,
                    "continuity_shift": clamp(deltas.get("continuity", 0.0)),
                    "volatility_shift": round(deltas.get("volatility", 0.0), 3),
                    "discourse_shift": clamp(deltas.get("discourse", 0.0)),
                    "temporal_shift": clamp(deltas.get("temporal", 0.0)),
                },
                "counterfactual_uncertainty": clamp(uncertainty + pressure * 0.14),
                "authority_boundary": "Simulation can prioritize human review, but cannot edit media or assert outcome truth.",
            }
        )
    output = base_artifact(method="deterministic_counterfactual_editorial_simulation_v1")
    output.update(
        {
            "counterfactual_scenarios": rows,
            "summary": {
                "scenario_count": len(rows),
                "best_readiness_shift": max([row["estimated_shifts"]["readiness_shift"] for row in rows], default=0.0),
                "mean_counterfactual_uncertainty": clamp(sum(row["counterfactual_uncertainty"] for row in rows) / max(len(rows), 1)),
            },
        }
    )
    return output
