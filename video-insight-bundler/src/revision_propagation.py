"""Proposal-only revision propagation estimates."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id


IMPACT = {
    "continuity": {"continuity": 0.1, "contradiction": -0.05, "readiness": 0.035},
    "rhetorical": {"continuity": 0.04, "discourse": 0.09, "readiness": 0.03},
    "pacing": {"temporal": 0.1, "volatility": -0.04, "readiness": 0.025},
    "structure": {"continuity": 0.05, "temporal": 0.04, "readiness": 0.02},
}


def build_revision_propagation(bundle, recommendation_dependencies: dict, editorial_pressure: dict | None = None) -> dict:
    nodes = recommendation_dependencies.get("recommendation_nodes") or []
    pressure_peak = float(((editorial_pressure or {}).get("summary") or {}).get("peak_cumulative_pressure_score") or 0.0)
    rows = []
    for node in nodes:
        family = node.get("family")
        profile = IMPACT.get(family, {"readiness": 0.01})
        uncertainty = clamp(0.22 + pressure_peak * 0.22 + (1.0 - float(node.get("confidence") or 0.0)) * 0.28)
        rows.append(
            {
                "propagation_id": deterministic_id("PROP", node.get("recommendation_node_id"), family, profile),
                "recommendation_node_id": node.get("recommendation_node_id"),
                "affected_segment_ids": node.get("affected_segment_ids") or [],
                "revision_family": family,
                "estimated_effects": {
                    "continuity_improvement_estimate": clamp(profile.get("continuity", 0.0)),
                    "contradiction_reduction_estimate": clamp(abs(profile.get("contradiction", 0.0))),
                    "temporal_rhythm_improvement_estimate": clamp(profile.get("temporal", 0.0)),
                    "discourse_improvement_estimate": clamp(profile.get("discourse", 0.0)),
                    "readiness_impact_estimate": clamp(profile.get("readiness", 0.0) * float(node.get("dependency_pressure") or 1.0)),
                    "volatility_reduction_estimate": clamp(abs(profile.get("volatility", 0.0))),
                },
                "propagation_uncertainty": uncertainty,
                "safety_class": "proposal_only_no_media_mutation",
            }
        )
    graph_edges = []
    for edge in recommendation_dependencies.get("dependency_edges") or []:
        graph_edges.append(
            {
                "propagation_edge_id": deterministic_id("PEDGE", edge.get("dependency_id")),
                "dependency_id": edge.get("dependency_id"),
                "from_recommendation_node_id": edge.get("from_recommendation_node_id"),
                "to_recommendation_node_id": edge.get("to_recommendation_node_id"),
                "propagation_type": edge.get("dependency_type"),
                "propagation_pressure": edge.get("interaction_pressure"),
            }
        )
    output = base_artifact(method="deterministic_revision_propagation_v1")
    output.update(
        {
            "propagation_estimates": rows,
            "propagation_edges": graph_edges,
            "summary": {
                "propagation_count": len(rows),
                "mean_readiness_impact_estimate": clamp(sum(row["estimated_effects"]["readiness_impact_estimate"] for row in rows) / max(len(rows), 1)),
                "mean_propagation_uncertainty": clamp(sum(row["propagation_uncertainty"] for row in rows) / max(len(rows), 1)),
                "revision_conflict_awareness": sum(1 for row in graph_edges if row["propagation_type"] == "blocking"),
            },
        }
    )
    return output
