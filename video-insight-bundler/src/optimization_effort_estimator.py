"""Estimate non-mutating optimization effort for ranked recommendations."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


EFFORT_ORDER = {
    "trivial adjustment": 1,
    "low effort": 2,
    "moderate effort": 3,
    "high effort": 4,
    "re-record candidate": 5,
    "structural rewrite candidate": 6,
    "full re-edit candidate": 7,
}


def build_optimization_effort_estimates(recommendation_ranking: dict, outputs: dict | None = None) -> dict:
    rows = []
    for rec in recommendation_ranking.get("ranked_recommendations") or []:
        category = rec.get("effort_estimate") or "moderate effort"
        effort_level = EFFORT_ORDER.get(category, 3)
        rows.append(
            {
                "effort_estimate_id": deterministic_id("EFFORT", rec.get("recommendation_rank_id"), category),
                "source_recommendation_rank_id": rec.get("recommendation_rank_id"),
                "source_review_item_id": rec.get("source_review_item_id"),
                "effort_category": category,
                "effort_level": effort_level,
                "production_effort": "high" if effort_level >= 5 else "medium" if effort_level >= 3 else "low",
                "editing_effort": "high" if category == "full re-edit candidate" else "medium" if effort_level >= 3 else "low",
                "risk": "high" if effort_level >= 5 else "medium" if rec.get("severity") == "high" else "low",
                "expected_benefit": rec.get("likely_benefit"),
                "governance_impact": rec.get("governance_severity"),
                "human_review_required": True,
                "mutation_required": False,
                "evidence_refs": rec.get("evidence_refs") or [],
            }
        )
    output = base_artifact(method="deterministic_optimization_effort_estimator_v1")
    output.update(
        {
            "optimization_effort_estimates_id": deterministic_id("OEFF", [(row["source_review_item_id"], row["effort_category"]) for row in rows]),
            "effort_estimates": rows,
            "summary": {"effort_estimate_count": len(rows), "high_effort_count": sum(1 for row in rows if row["effort_level"] >= 5)},
        }
    )
    return output
