"""Reusable metric insight card registry for expert dashboard pages."""

from __future__ import annotations

from intelligence_common import base_artifact
from stability import deterministic_id


def _confidence(status: str, evidence_count: int) -> str:
    if status == "concern" and evidence_count >= 2:
        return "high"
    if status in {"good", "caution", "concern"}:
        return "medium"
    return "review"


def build_metric_card_registry(outputs: dict, benchmark_registry: dict, threshold_registry: dict) -> dict:
    benchmarks_by_metric = {}
    for row in benchmark_registry.get("benchmark_comparisons") or []:
        benchmarks_by_metric.setdefault(row.get("metric_id"), []).append(row)
    overlays = {row.get("graph_id"): row for row in threshold_registry.get("threshold_overlays") or []}
    guidance = outputs.get("optimization_guidance_index", {}).get("guidance_items") or []
    guidance_by_metric = {}
    for row in guidance:
        guidance_by_metric.setdefault(row.get("trigger_metric_or_pattern"), []).append(row)
    cards = []
    for graph in (outputs.get("graph_interpretation_index") or {}).get("graph_interpretations") or []:
        metric_id = graph.get("metric_id")
        bench_count = len(benchmarks_by_metric.get(metric_id, []))
        actions = [row.get("recommended_action") for row in guidance_by_metric.get(metric_id, [])] or graph.get("optimization_actions") or []
        cards.append(
            {
                "metric_card_id": deterministic_id("MCARD", graph.get("graph_id"), metric_id, graph.get("status")),
                "metric_id": metric_id,
                "metric_name": graph.get("graph_title"),
                "category_tag": graph.get("subsystem"),
                "severity_badge": graph.get("status"),
                "confidence_badge": _confidence(graph.get("status"), len(graph.get("evidence_refs") or []) + bench_count),
                "mini_graph_preview": graph.get("graph_path"),
                "current_score_or_value": graph.get("current_observed_values"),
                "benchmark_comparison": {
                    "comparison_count": bench_count,
                    "summary": "Compared against local corpus distributions when metric values are available.",
                },
                "interpretation_summary": graph.get("current_interpretation"),
                "current_status": graph.get("status"),
                "top_optimization_actions": actions[:3],
                "footer_links": {
                    "more_details": graph.get("detail_page_path"),
                    "open_full_analysis": graph.get("graph_path"),
                    "compare_videos": "visualizations/compare_workflows.html",
                },
                "supported_modes": ["compact", "expanded", "dashboard", "detail-page"],
                "threshold_overlay_ref": overlays.get(graph.get("graph_id"), {}).get("threshold_overlay_id"),
                "evidence_refs": graph.get("evidence_refs") or [],
            }
        )
    output = base_artifact(method="deterministic_metric_card_system_v1")
    output.update(
        {
            "metric_card_registry_id": deterministic_id("MCREG", [(row["metric_id"], row["severity_badge"], row["confidence_badge"]) for row in cards]),
            "metric_cards": cards,
            "ui_primitives": [
                "MetricCard", "MetricDetailPage", "GraphLegend", "ThresholdOverlay", "OptimizationPanel",
                "InterpretationBadge", "RecommendationBlock", "EvidencePanel", "BenchmarkComparison",
                "SegmentDrilldownTable", "ComparePanel", "SeverityRibbon", "ConfidenceBadge",
                "ThresholdBadge", "NavigationSidebar", "ExpandableExplanation", "StickyLegend",
                "TooltipDefinition", "InsightSummaryPanel",
            ],
            "summary": {"metric_card_count": len(cards)},
        }
    )
    return output
