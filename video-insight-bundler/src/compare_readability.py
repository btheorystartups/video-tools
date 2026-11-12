"""Readability summaries for side-by-side temporal comparisons."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_compare_readability_registry(compare_registry: dict, temporal_index: dict, previews: dict) -> dict:
    entries = []
    by_video = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        by_video.setdefault(entry.get("source_video"), []).append(entry)
    for compare in compare_registry.get("temporal_compare_workflows") or []:
        left = by_video.get(compare.get("left_video"), [])
        right = by_video.get(compare.get("right_video"), [])
        entries.append(
            {
                "compare_readability_id": deterministic_id("CMPREAD", compare.get("temporal_compare_id")),
                "source_compare_id": compare.get("temporal_compare_id"),
                "left_video": compare.get("left_video"),
                "right_video": compare.get("right_video"),
                "aligned_timeline_scale": {"left_segment_count": len(left), "right_segment_count": len(right), "scale_basis": "duration-normalized local review scale"},
                "matched_segment_summaries": [
                    {"left_segment": (left[i].get("segment_id") if i < len(left) else None), "right_segment": (right[i].get("segment_id") if i < len(right) else None)}
                    for i in range(max(len(left), len(right), 1))[:10]
                ],
                "delta_badges": compare.get("metric_deltas") or {},
                "severity_deltas": compare.get("metric_deltas") or {},
                "recommendation_deltas": {"directional_only": True},
                "benchmark_deltas": {"basis": "local corpus heuristic"},
                "side_by_side_evidence_previews": [row.get("evidence_preview_id") for row in (previews.get("evidence_previews") or [])[:6]],
                "compare_summary_cards": ["Aligned scale", "Severity delta", "Evidence preview", "Optimization implication"],
                "interpretation_differences": compare.get("interpretation_delta"),
                "optimization_implications": compare.get("optimization_implications"),
                "html_page": compare.get("detail_page"),
                "non_claim_limitation": LIMITATION,
            }
        )
    output = base_artifact(method="deterministic_compare_readability_v1")
    output.update({"compare_readability_registry_id": deterministic_id("CMPREADREG", [row["compare_readability_id"] for row in entries]), "compare_readability_entries": entries, "summary": {"compare_readability_count": len(entries)}, "limitations": [LIMITATION]})
    return output
