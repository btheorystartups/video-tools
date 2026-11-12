"""Deterministic static compare workflow registry."""

from __future__ import annotations

from itertools import combinations

from intelligence_common import base_artifact, num
from stability import deterministic_id


def build_compare_workflow_registry(outputs: dict, benchmark_registry: dict | None = None) -> dict:
    videos = (outputs.get("corpus_index") or {}).get("videos") or []
    rows = []
    for left, right in combinations(videos[:8], 2):
        readiness_delta = round(num(left.get("readiness_score")) - num(right.get("readiness_score")), 3)
        pressure_delta = round(num(left.get("peak_pressure_score")) - num(right.get("peak_pressure_score")), 3)
        workflow_id = deterministic_id("CMP", left.get("corpus_item_id"), right.get("corpus_item_id"))
        rows.append(
            {
                "compare_workflow_id": workflow_id,
                "workflow_type": "video_to_video",
                "left_video": left.get("source_video"),
                "right_video": right.get("source_video"),
                "left_corpus_item_id": left.get("corpus_item_id"),
                "right_corpus_item_id": right.get("corpus_item_id"),
                "detail_page": f"visualizations/detail/compare_{workflow_id.lower()}.html",
                "comparison_metrics": {
                    "readiness_delta": readiness_delta,
                    "pressure_delta": pressure_delta,
                    "structural_coherence_delta": round(num(left.get("structural_coherence_score")) - num(right.get("structural_coherence_score")), 3),
                },
                "interpretation": "Use deltas to identify review patterns; do not treat differences as proof of audience behavior.",
                "recommended_use": "Compare pacing, pressure, and readiness before prioritizing edits.",
                "evidence_refs": ["corpus/corpus_index.json", "dashboard/benchmark_comparison_registry.json"],
            }
        )
    if videos:
        for video in videos[:8]:
            workflow_id = deterministic_id("CMPV", video.get("corpus_item_id"))
            rows.append(
                {
                    "compare_workflow_id": workflow_id,
                    "workflow_type": "video_to_corpus",
                    "left_video": video.get("source_video"),
                    "right_video": "Corpus median",
                    "left_corpus_item_id": video.get("corpus_item_id"),
                    "right_corpus_item_id": None,
                    "detail_page": f"visualizations/detail/compare_{workflow_id.lower()}.html",
                    "comparison_metrics": {
                        "readiness_score": video.get("readiness_score"),
                        "peak_pressure_score": video.get("peak_pressure_score"),
                        "structural_coherence_score": video.get("structural_coherence_score"),
                    },
                    "interpretation": "Shows where this video sits against the current local corpus.",
                    "recommended_use": "Use for corpus-to-video prioritization and accepted-style review.",
                    "evidence_refs": ["corpus/corpus_index.json", "dashboard/benchmark_comparison_registry.json"],
                }
            )
    output = base_artifact(method="deterministic_compare_workflows_v1")
    output.update(
        {
            "compare_workflow_registry_id": deterministic_id("CMPREG", [row["compare_workflow_id"] for row in rows]),
            "compare_workflows": rows,
            "summary": {"compare_workflow_count": len(rows), "video_count": len(videos)},
        }
    )
    return output
