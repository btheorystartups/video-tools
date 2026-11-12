"""Static HTML renderers for Phase 32 expert detail pages."""

from __future__ import annotations

from pathlib import Path

from dashboard_layout import badge, e, page, panel


def render_metric_card_gallery(metric_registry: dict, links: list[tuple[str, str]]) -> str:
    cards = metric_registry.get("metric_cards") or []
    body = "<section class='filter-bar' aria-label='Metric filters'><span>Filters:</span><span>category</span><span>severity</span><span>confidence</span></section>"
    body += "<section class='graph-card-grid'>" + "".join(
        "<article class='graph-card metric-insight-card'>"
        f"<div class='card-top'><h3>{e(card.get('metric_name'))}</h3>{badge(card.get('severity_badge'))}</div>"
        f"<p><span class='badge'>{e(card.get('category_tag'))}</span> <span class='badge'>{e(card.get('confidence_badge'))} confidence</span></p>"
        f"<figure class='graph compact'><img src='../{e(card.get('mini_graph_preview'))}' alt='{e(card.get('metric_name'))}'></figure>"
        f"<p><strong>Current:</strong> {e(card.get('interpretation_summary'))}</p>"
        f"<p><strong>Benchmark:</strong> {e((card.get('benchmark_comparison') or {}).get('summary'))}</p>"
        f"<p><strong>Actions:</strong> {e('; '.join(card.get('top_optimization_actions') or []))}</p>"
        f"<a class='more-link' href='{e((card.get('footer_links') or {}).get('more_details', '').replace('visualizations/', ''))}'>More Details</a>"
        " <a class='more-link' href='compare_workflows.html'>Compare Videos</a>"
        "</article>"
        for card in cards
    ) + "</section>"
    body += panel("Non-Claims", ["Metric cards are deterministic review aids.", "They do not predict audience behavior or apply edits."])
    return page("Metric Card Gallery", "Expert UI Components", "metric_card_gallery.html", body, links)


def render_registry_cards(title: str, active: str, rows: list[dict], links: list[tuple[str, str]], fields: list[str]) -> str:
    body = "<section class='graph-card-grid'>" + "".join(
        "<article class='graph-card'>"
        + "".join(f"<p><strong>{e(field.replace('_', ' ').title())}:</strong> {e(row.get(field))}</p>" for field in fields)
        + "</article>"
        for row in rows
    ) + "</section>"
    body += panel("Limitations", ["All values are deterministic local review heuristics.", "Human review is required before production or editorial changes."])
    return page(title, "Expert Review", active, body, links)


def render_segment_detail_page(page_row: dict, segment_rows: list[dict], links: list[tuple[str, str]]) -> str:
    detail_links = [(label, href if href.startswith("../") else f"../{href}") for label, href in links]
    rows = "".join(
        "<tr>"
        f"<td>{e(row.get('segment_id'))}</td><td>{e(row.get('start_sec'))}-{e(row.get('end_sec'))}</td><td>{badge(row.get('severity'))}</td>"
        f"<td>{e(row.get('related_metrics'))}</td><td>{e(', '.join(row.get('related_recommendations') or []))}</td>"
        f"<td>{e(row.get('suggested_review_action'))}</td>"
        "</tr>"
        for row in segment_rows
    ) or "<tr><td colspan='6'>No segment rows available.</td></tr>"
    body = (
        panel("Segment Review Scope", f"Source video: {page_row.get('source_video')}")
        + "<section class='panel'><h2>Segment Drilldown Table</h2><table><thead><tr><th>Segment</th><th>Time</th><th>Severity</th><th>Metrics</th><th>Recommendations</th><th>Review Action</th></tr></thead><tbody>"
        + rows
        + "</tbody></table></section>"
        + panel("What Not To Infer", ["Segment severity is not an audience prediction.", "No edit is applied automatically.", "Review source evidence before changing pacing, visuals, or structure."])
        + panel("Limitations", ["Segment drilldowns are deterministic local heuristics.", "They do not diagnose emotion, infer intent, or apply edits."])
    )
    return page("Segment Drilldown", "Segment Evidence", "../segment_drilldown_index.html", body, detail_links).replace("../static_assets/report.css", "../../static_assets/report.css").replace("href='dashboard.html'", "href='../dashboard.html'").replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'").replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'").replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")


def render_compare_detail_page(workflow: dict, links: list[tuple[str, str]]) -> str:
    detail_links = [(label, href if href.startswith("../") else f"../{href}") for label, href in links]
    body = (
        panel("Compare Scope", [f"Workflow: {workflow.get('workflow_type')}", f"Left: {workflow.get('left_video')}", f"Right: {workflow.get('right_video')}"])
        + panel("Comparison Metrics", str(workflow.get("comparison_metrics") or {}))
        + panel("Interpretation", workflow.get("interpretation") or "")
        + panel("Limitations", ["Compare pages are deterministic review aids.", "They do not prove causal quality differences or predict audience behavior."])
    )
    return page("Compare Detail", "Compare Workflow", "../compare_workflows.html", body, detail_links).replace("../static_assets/report.css", "../../static_assets/report.css").replace("href='dashboard.html'", "href='../dashboard.html'").replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'").replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'").replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")


def render_benchmark_detail_page(row: dict, links: list[tuple[str, str]]) -> str:
    detail_links = [(label, href if href.startswith("../") else f"../{href}") for label, href in links]
    body = (
        panel("Benchmark Scope", [f"Metric: {row.get('display_name')}", f"Video: {row.get('source_video')}"])
        + panel("Current Position", [f"Value: {row.get('current_value')}", f"Corpus median: {row.get('corpus_median')}", f"Percentile: {row.get('percentile_position')}", f"Classification: {row.get('balanced_elevated_extreme_classification')}"])
        + panel("Uncertainty Notes", row.get("uncertainty_notes") or [])
        + panel("Limitations", ["Local benchmarks are not universal quality standards.", "Human review is required before editorial changes."])
    )
    return page("Benchmark Detail", "Benchmark Comparison", "../benchmark_comparison_index.html", body, detail_links).replace("../static_assets/report.css", "../../static_assets/report.css").replace("href='dashboard.html'", "href='../dashboard.html'").replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'").replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'").replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")
