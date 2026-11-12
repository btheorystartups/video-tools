"""Threshold overlay registry for static expert graph annotations."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


def build_threshold_overlay_registry(graph_index: dict, expert_metric_ranges: dict) -> dict:
    ranges = {row.get("metric_id"): row for row in expert_metric_ranges.get("metric_ranges") or []}
    rows = []
    for graph in graph_index.get("graph_interpretations") or []:
        metric_id = graph.get("metric_id")
        metric_range = ranges.get(metric_id, {})
        rows.append(
            {
                "threshold_overlay_id": deterministic_id("TOVER", graph.get("graph_id"), metric_id),
                "graph_id": graph.get("graph_id"),
                "metric_id": metric_id,
                "graph_path": graph.get("graph_path"),
                "overlay_type": "static_threshold_band",
                "bands": [
                    {"label": "good", "range": metric_range.get("good_range") or {"qualitative": "review"}, "color": "#2f7d62"},
                    {"label": "caution", "range": metric_range.get("caution_range") or {"qualitative": "review"}, "color": "#b7791f"},
                    {"label": "concern", "range": metric_range.get("concern_range") or {"qualitative": "review"}, "color": "#b94a48"},
                ],
                "current_value_indicator": graph.get("current_observed_values") or {},
                "tooltip_definition": {
                    "exact_value": graph.get("current_observed_values") or {},
                    "benchmark_position": "See benchmark comparison registry when available.",
                    "threshold_category": graph.get("status"),
                    "short_interpretation": graph.get("current_interpretation"),
                    "optimization_hint": "; ".join(graph.get("optimization_actions") or []),
                },
                "accessibility_notes": ["Uses color plus text labels; does not rely on color alone."],
                "evidence_refs": graph.get("evidence_refs") or [],
            }
        )
    output = base_artifact(method="deterministic_threshold_overlay_v1")
    output.update(
        {
            "threshold_overlay_registry_id": deterministic_id("TOREG", [(row["graph_id"], row["metric_id"]) for row in rows]),
            "threshold_overlays": rows,
            "summary": {"threshold_overlay_count": len(rows)},
        }
    )
    return output
