"""Comparative recommendation convergence and divergence analysis."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, clamp, deterministic_id


def build_comparative_recommendations(analyses: list[dict], structural_patterns: dict, creator_evolution: dict) -> dict:
    counts: Counter = Counter()
    for analysis in analyses:
        counts.update(row.get("issue_type") for row in (analysis.get("recommendations") or {}).get("recommendations", []) if row.get("issue_type"))
    rows = []
    for issue, count in counts.most_common():
        rows.append(
            {
                "comparative_recommendation_id": deterministic_id("COMPREC", issue, count, len(analyses)),
                "issue_type": issue,
                "occurrence_count": count,
                "convergence_score": clamp(count / max(len(analyses), 1)),
                "recommendation_class": "recurring_creator_pattern" if count >= max(2, len(analyses)) else "single_or_emerging_pattern",
            }
        )
    output = base_artifact(method="deterministic_comparative_recommendation_reasoning_v1")
    output.update(
        {
            "comparative_recommendations": rows,
            "recommendation_convergence_graph": [
                {"from_issue_type": left.get("issue_type"), "to_issue_type": right.get("issue_type"), "convergence_weight": min(left.get("convergence_score"), right.get("convergence_score"))}
                for index, left in enumerate(rows)
                for right in rows[index + 1:]
            ],
            "summary": {
                "unique_recommendation_family_count": len(rows),
                "recurring_recommendation_count": sum(1 for row in rows if row["recommendation_class"] == "recurring_creator_pattern"),
                "creator_evolution_classification": creator_evolution.get("classification"),
                "structural_pattern_count": (structural_patterns.get("summary") or {}).get("recurring_pattern_count"),
            },
        }
    )
    return output
