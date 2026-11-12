"""Static expert dashboard navigation manifest."""

from __future__ import annotations

from stability import STATUS_COMPLETE, deterministic_id


def build_dashboard_navigation_manifest(outputs: dict) -> dict:
    sections = [
        ("overview", "Overview", "corpus_dashboard.html", ["classification", "readiness", "tier"]),
        ("metrics", "Metric Cards", "metric_card_gallery.html", ["category", "severity", "confidence"]),
        ("benchmarks", "Benchmarks", "benchmark_comparison_index.html", ["metric", "percentile", "classification"]),
        ("recommendations", "Recommendation Priority", "recommendation_priority_dashboard.html", ["severity", "effort", "confidence"]),
        ("effort", "Optimization Effort", "optimization_effort_dashboard.html", ["effort", "risk", "benefit"]),
        ("segments", "Segment Drilldowns", "segment_drilldown_index.html", ["video", "severity", "metric"]),
        ("compare", "Compare Workflows", "compare_workflows.html", ["workflow", "video", "metric"]),
    ]
    rows = [
        {
            "section_id": section_id,
            "label": label,
            "href": href,
            "anchor": f"#{section_id}",
            "filter_keys": filters,
            "sticky_nav_enabled": True,
            "progressive_disclosure_enabled": True,
        }
        for section_id, label, href, filters in sections
    ]
    return {
        "analysis_status": STATUS_COMPLETE,
        "method": "deterministic_dashboard_navigation_v1",
        "dashboard_navigation_manifest_id": deterministic_id("DNAV", [(row["section_id"], row["href"]) for row in rows]),
        "sections": rows,
        "filters": sorted({item for row in rows for item in row["filter_keys"]}),
        "responsive_layout": "sticky sidebar on desktop, stacked navigation on narrow screens",
        "accessibility_notes": ["Section anchors are deep-linkable.", "Controls use labels and visible text, not color alone."],
        "summary": {"section_count": len(rows)},
        "limitations": ["Navigation is static HTML and optional local CSS only."],
    }
