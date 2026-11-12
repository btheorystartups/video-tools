"""Static annotation and tooltip definitions for expert graph pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


def build_graph_annotation_registry(graph_index: dict, benchmark_registry: dict, threshold_registry: dict) -> dict:
    benchmark_by_metric = {}
    for row in benchmark_registry.get("benchmark_comparisons") or []:
        benchmark_by_metric.setdefault(row.get("metric_id"), []).append(row)
    overlays = {row.get("graph_id"): row for row in threshold_registry.get("threshold_overlays") or []}
    annotations = []
    for graph in graph_index.get("graph_interpretations") or []:
        metric_id = graph.get("metric_id")
        benchmarks = benchmark_by_metric.get(metric_id, [])
        annotations.append(
            {
                "graph_annotation_id": deterministic_id("GANN", graph.get("graph_id"), graph.get("status")),
                "graph_id": graph.get("graph_id"),
                "graph_path": graph.get("graph_path"),
                "metric_id": metric_id,
                "annotation_labels": [
                    {"label": "Current status", "value": graph.get("status")},
                    {"label": "Benchmark comparisons", "value": len(benchmarks)},
                    {"label": "Optimization hint", "value": "; ".join(graph.get("optimization_actions") or [])},
                ],
                "tooltip_explanations": [
                    {
                        "trigger": "current_value",
                        "content": graph.get("current_interpretation"),
                        "optimization_hint": "; ".join(graph.get("optimization_actions") or []),
                    },
                    {
                        "trigger": "threshold_band",
                        "content": "Good, caution, and concern bands are conservative local review heuristics.",
                        "optimization_hint": "Use as a review prompt, not an edit command.",
                    },
                ],
                "threshold_overlay_ref": overlays.get(graph.get("graph_id"), {}).get("threshold_overlay_id"),
                "mini_insights": [
                    graph.get("why_it_matters"),
                    "Human review is required before production or editorial changes.",
                ],
                "evidence_refs": graph.get("evidence_refs") or [],
            }
        )
    output = base_artifact(method="deterministic_interactive_graph_annotations_v1")
    output.update(
        {
            "interactive_graph_annotation_registry_id": deterministic_id("GANNREG", [row["graph_annotation_id"] for row in annotations]),
            "graph_annotations": annotations,
            "summary": {"graph_annotation_count": len(annotations)},
        }
    )
    return output
