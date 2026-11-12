"""Rule-based recurring structural-pattern mining."""

from __future__ import annotations

from collections import Counter

from intelligence_common import base_artifact, clamp, deterministic_id


def build_structural_pattern_mining(analyses: list[dict]) -> dict:
    motif_counts: Counter = Counter()
    recommendation_counts: Counter = Counter()
    contradiction_regions = []
    rows = []
    for analysis in analyses:
        sequence = analysis.get("sequence_structure") or {}
        pressure = analysis.get("editorial_pressure") or {}
        recs = (analysis.get("recommendations") or {}).get("recommendations") or []
        group_classes = [row.get("group_class") for row in sequence.get("segment_groups", []) if row.get("group_class")]
        motif_counts.update(group_classes)
        recommendation_counts.update(row.get("issue_type") for row in recs if row.get("issue_type"))
        chronic = (pressure.get("summary") or {}).get("chronic_pressure_regions") or []
        contradiction_regions.extend({"analysis_dir": analysis.get("analysis_dir"), **row} for row in chronic)
        rows.append(
            {
                "pattern_sample_id": deterministic_id("PAT", analysis.get("analysis_dir"), group_classes, [row.get("issue_type") for row in recs]),
                "analysis_dir": analysis.get("analysis_dir"),
                "narrative_shape": "->".join(group_classes) if group_classes else "limited",
                "recurring_pacing_motifs": group_classes,
                "recommendation_families": dict(sorted(Counter(row.get("issue_type") for row in recs if row.get("issue_type")).items())),
                "chronic_pressure_region_count": len(chronic),
            }
        )
    patterns = [
        {
            "pattern_id": deterministic_id("RPAT", key, value),
            "pattern_type": key,
            "occurrence_count": value,
            "pattern_pressure": clamp(value / max(len(analyses), 1)),
        }
        for key, value in sorted(motif_counts.items())
    ]
    output = base_artifact(method="deterministic_structural_pattern_mining_v1")
    output.update(
        {
            "pattern_samples": rows,
            "recurring_patterns": patterns,
            "recurring_contradiction_regions": contradiction_regions,
            "recurring_recommendation_clusters": [{"issue_type": key, "count": value} for key, value in recommendation_counts.most_common()],
            "summary": {
                "analysis_count": len(analyses),
                "recurring_pattern_count": len(patterns),
                "chronic_pressure_region_count": len(contradiction_regions),
            },
        }
    )
    return output
