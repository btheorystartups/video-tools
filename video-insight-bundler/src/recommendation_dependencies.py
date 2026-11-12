"""Recommendation dependency graph reasoning."""

from __future__ import annotations

from intelligence_common import base_artifact, clamp, deterministic_id, recommendation_rows


def _severity_weight(value: str | None) -> float:
    return {"high": 1.0, "medium": 0.68, "low": 0.38}.get(value or "", 0.45)


def _family(issue_type: str | None) -> str:
    text = issue_type or "general"
    if "pacing" in text or "energy" in text:
        return "pacing"
    if "topic" in text or "transition" in text or "continuity" in text:
        return "continuity"
    if "rhetorical" in text or "claim" in text or "question" in text:
        return "rhetorical"
    if "opening" in text or "closing" in text:
        return "structure"
    return text.split("_", 1)[0]


def build_recommendation_dependencies(bundle, editorial_pressure: dict | None = None) -> dict:
    recs = recommendation_rows(bundle)
    nodes = []
    for index, rec in enumerate(recs, start=1):
        seed = [rec.get("issue_type"), rec.get("affected_segment_ids"), rec.get("suggested_edit")]
        nodes.append(
            {
                "recommendation_node_id": deterministic_id("RECDEP", seed),
                "recommendation_index": index,
                "issue_type": rec.get("issue_type"),
                "family": _family(rec.get("issue_type")),
                "severity": rec.get("severity"),
                "confidence": rec.get("confidence"),
                "affected_segment_ids": rec.get("affected_segment_ids") or [],
                "dependency_pressure": clamp(_severity_weight(rec.get("severity")) * 0.55 + float(rec.get("confidence") or 0.0) * 0.45),
            }
        )
    edges = []
    for left_index, left in enumerate(nodes):
        left_segments = set(left.get("affected_segment_ids") or [])
        for right in nodes[left_index + 1:]:
            right_segments = set(right.get("affected_segment_ids") or [])
            overlap = len(left_segments & right_segments)
            same_family = left.get("family") == right.get("family")
            if overlap or same_family:
                relation = "reinforcing" if same_family else "overlapping"
                pressure = clamp((overlap / max(len(left_segments | right_segments), 1)) * 0.62 + (0.32 if same_family else 0.0))
            elif left.get("family") == "pacing" and right.get("family") in {"continuity", "rhetorical"}:
                relation = "prerequisite"
                pressure = 0.42
            elif left.get("family") == "continuity" and right.get("family") == "structure":
                relation = "blocking"
                pressure = 0.36
            else:
                continue
            edges.append(
                {
                    "dependency_id": deterministic_id("DEP", left["recommendation_node_id"], right["recommendation_node_id"], relation),
                    "from_recommendation_node_id": left["recommendation_node_id"],
                    "to_recommendation_node_id": right["recommendation_node_id"],
                    "dependency_type": relation,
                    "interaction_pressure": pressure,
                    "shared_segment_ids": sorted(left_segments & right_segments),
                    "explanation": f"{relation} recommendation interaction detected by deterministic family and segment overlap rules.",
                }
            )
    cascades = [
        {
            "cascade_id": deterministic_id("CASCADE", edge["dependency_id"]),
            "seed_dependency_id": edge["dependency_id"],
            "cascade_type": edge["dependency_type"],
            "estimated_cascade_pressure": edge["interaction_pressure"],
        }
        for edge in edges
        if edge["dependency_type"] in {"prerequisite", "blocking", "reinforcing"}
    ]
    pressure = (editorial_pressure or {}).get("summary") or {}
    output = base_artifact(method="deterministic_recommendation_dependency_graph_v1")
    output.update(
        {
            "recommendation_nodes": nodes,
            "dependency_edges": edges,
            "cascading_recommendations": cascades,
            "summary": {
                "recommendation_count": len(nodes),
                "dependency_count": len(edges),
                "conflicting_recommendation_count": sum(1 for row in edges if row["dependency_type"] in {"blocking"}),
                "reinforcing_recommendation_count": sum(1 for row in edges if row["dependency_type"] == "reinforcing"),
                "cascade_count": len(cascades),
                "recommendation_dependency_pressure": clamp(sum(row["interaction_pressure"] for row in edges) / max(len(edges), 1)),
                "editorial_pressure_peak": pressure.get("peak_cumulative_pressure_score"),
            },
        }
    )
    return output
