"""Enhanced static timeline workstation pages and manifest."""

from __future__ import annotations

from pathlib import Path

from dashboard_layout import e, page, panel
from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def _workstation_page(title: str, section: str, active: str, body: str, links: list[tuple[str, str]], depth: str = "workstation") -> str:
    html = page(title, section, active, body, links)
    if depth == "workstation":
        html = html.replace("../static_assets/report.css", "../../static_assets/report.css")
        html = html.replace("href='dashboard.html'", "href='../dashboard.html'")
        html = html.replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'")
        html = html.replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'")
        html = html.replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")
    elif depth == "timeline":
        html = html.replace("../static_assets/report.css", "../../static_assets/report.css")
        html = html.replace("href='dashboard.html'", "href='../dashboard.html'")
        html = html.replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'")
        html = html.replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'")
        html = html.replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")
    return html


def build_workstation_manifest(outputs: dict) -> dict:
    pages = [
        "visualizations/workstation/workstation_index.html",
        "visualizations/workstation/timeline_workstation_overview.html",
        "visualizations/workstation/overlay_filter_console.html",
        "visualizations/workstation/temporal_heatmap_index.html",
        "visualizations/workstation/review_flow_shortcuts.html",
        "visualizations/workstation/review_state_summary.html",
        "visualizations/workstation/compare_readability_index.html",
        "visualizations/timeline/enhanced_corpus_timeline_overview.html",
    ]
    pages.extend(row.get("timeline_page") for row in (outputs.get("timeline_review_index") or {}).get("video_timeline_pages") or [])
    output = base_artifact(method="deterministic_timeline_workstation_manifest_v1")
    output.update(
        {
            "workstation_manifest_id": deterministic_id("WSMAN", pages),
            "classification": "operational beta+",
            "static_local_only": True,
            "external_runtime_dependency_introduced": False,
            "media_mutation_performed": False,
            "pages": pages,
            "artifact_refs": {
                "timeline_minimaps": "workstation/timeline_minimap_registry.json",
                "overlay_lanes": "workstation/overlay_lane_registry.json",
                "overlay_filters": "workstation/overlay_filter_registry.json",
                "review_shortcuts": "workstation/review_flow_shortcuts.json",
                "context_panels": "workstation/persistent_context_registry.json",
                "evidence_previews": "workstation/inline_evidence_preview_index.json",
                "recommendation_drawers": "workstation/recommendation_drawer_index.json",
                "temporal_heatmaps": "workstation/temporal_heatmap_registry.json",
                "compare_readability": "workstation/compare_readability_registry.json",
                "review_state_summary": "workstation/review_state_summary.json",
                "crosslinks": "workstation/workstation_crosslink_index.json",
            },
            "workflow_path": ["corpus overview", "video", "timeline", "segment", "metric spike", "recommendation", "evidence", "optimization path"],
            "summary": {"page_count": len(pages)},
            "limitations": [LIMITATION],
        }
    )
    return output


def _severity_badge(value: str | None) -> str:
    return f"<span class='severity-badge {e(value or 'review')}'>{e(value or 'review')}</span>"


def _mini_bar(bands: list[dict]) -> str:
    if not bands:
        return "<div class='empty-state'>No timeline regions available.</div>"
    spans = []
    for band in bands:
        spans.append(f"<a class='minimap-cell {e(band.get('severity'))}' href='#{e(band.get('timeline_anchor'))}' title='{e(band.get('segment_id'))}'></a>")
    return "<div class='timeline-minimap'>" + "".join(spans) + "</div>"


def _segment_card(entry: dict, previews: list[dict], drawers: list[dict]) -> str:
    severity = (entry.get("highest_severity_signal") or {}).get("severity")
    signal = (entry.get("highest_severity_signal") or {}).get("signal")
    preview_html = "".join(f"<li><a href='{e(_rel_from_timeline(row.get('open_related_detail_page_link')))}'>{e(row.get('evidence_title'))}</a></li>" for row in previews[:3])
    drawer_html = "".join(f"<li><a href='../recommendation_traceability.html#{e(row.get('recommendation_id'))}'>{e(row.get('title'))}</a></li>" for row in drawers[:3])
    return (
        f"<article id='segment-{e(entry.get('segment_id'))}' class='segment-card compact {e(severity)}' data-severity='{e(severity)}'>"
        f"<div class='card-top'><h3>{e(entry.get('segment_id'))}</h3>{_severity_badge(severity)}</div>"
        f"<p><strong>{e(entry.get('timestamp_start'))}-{e(entry.get('timestamp_end'))} sec</strong> / {e(signal)}</p>"
        f"<p>{e(entry.get('suggested_review_action'))}</p>"
        f"<div class='mini-columns'><div><h4>Evidence</h4><ul>{preview_html or '<li>No preview available</li>'}</ul></div><div><h4>Recommendations</h4><ul>{drawer_html or '<li>No linked drawer</li>'}</ul></div></div>"
        "</article>"
    )


def _rel_from_timeline(path: str | None) -> str:
    if not path:
        return "#"
    path = path.replace("\\", "/")
    if path.startswith("visualizations/timeline/"):
        return Path(path).name
    if path.startswith("visualizations/"):
        return "../" + path.split("visualizations/", 1)[1]
    return "../../" + path


def render_enhanced_video_timeline_page(video_page: dict, outputs: dict, links: list[tuple[str, str]]) -> str:
    video_id = video_page.get("video_id")
    temporal = outputs.get("temporal_evidence_index") or {}
    minimap = next((row for row in (outputs.get("timeline_minimap_registry") or {}).get("minimaps") or [] if row.get("video_id") == video_id), {})
    entries = [row for row in temporal.get("temporal_evidence_entries") or [] if row.get("video_id") == video_id]
    lanes = [row for row in (outputs.get("overlay_lane_registry") or {}).get("lanes") or [] if row.get("video_id") == video_id]
    previews = outputs.get("inline_evidence_preview_index") or {}
    drawers = outputs.get("recommendation_drawer_index") or {}
    shortcuts = outputs.get("review_flow_shortcuts") or {}
    review_state = outputs.get("review_state_summary") or {}
    preview_by_seg = {}
    for row in previews.get("evidence_previews") or []:
        preview_by_seg.setdefault((row.get("video_id"), row.get("segment_id")), []).append(row)
    drawer_by_seg = {}
    for row in drawers.get("drawers") or []:
        drawer_by_seg.setdefault((video_id, row.get("affected_segment")), []).append(row)
    lane_html = "".join(
        f"<details class='overlay-lane' {'open' if row.get('collapse_state_default') == 'expanded' else ''}><summary>{e(row.get('lane_label'))} {_severity_badge('high' if (row.get('severity_summary') or {}).get('high') else 'review')} <span>{e(row.get('overlay_count'))}</span></summary><p>{e(row.get('explanation'))}</p></details>"
        for row in lanes
    )
    quick = "".join(f"<a class='button' href='{e(_rel_from_timeline(row.get('target_path')))}#{e(row.get('target_anchor'))}'>{e(row.get('label'))}</a>" for row in (shortcuts.get("shortcuts") or [])[:8])
    cards = "".join(_segment_card(entry, preview_by_seg.get((video_id, entry.get("segment_id")), []), drawer_by_seg.get((video_id, entry.get("segment_id")), [])) for entry in entries)
    context = panel("Persistent Context", [f"Video: {video_id}", f"Recommendations: {review_state.get('total_recommendations')}", f"Unresolved blockers: {review_state.get('unresolved_blockers')}", "Human review required before changes."])
    empty_overlays = '<p class="empty-state">No overlays available.</p>'
    empty_segments = '<p class="empty-state">No segments available.</p>'
    body = (
        f"<section class='workstation-shell'><div class='workstation-main'>"
        f"<section class='panel limitation-panel'><h2>Limitation</h2><p>{e(LIMITATION)}</p></section>"
        f"<section class='panel sticky-legend'><h2>Timeline Minimap</h2>{_mini_bar(minimap.get('severity_bands') or [])}<p class='muted'>What this means: darker regions are candidate issue clusters for human review, not proof of quality problems.</p></section>"
        f"<section class='panel'><h2>Quick Jumps</h2><div class='button-row'>{quick}</div></section>"
        f"<section class='panel'><h2>Overlay Lanes</h2>{lane_html or empty_overlays}</section>"
        f"<section class='segment-grid dense'>{cards or empty_segments}</section>"
        f"</div><aside class='context-panel'>{context}<div class='panel'><h2>Related</h2><div class='link-grid'><a href='../temporal_evidence_index.html'>Evidence index</a><a href='../recommendation_traceability.html'>Recommendations</a><a href='../governance_diagnostics.html'>Governance</a><a href='../workstation/compare_readability_index.html'>Compare readability</a></div></div></aside></section>"
    )
    return _workstation_page(f"Enhanced Timeline {video_id}", "Timeline Workstation", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links], depth="timeline")


def render_enhanced_corpus_timeline_overview(outputs: dict, links: list[tuple[str, str]]) -> str:
    rows = []
    for minimap in (outputs.get("timeline_minimap_registry") or {}).get("minimaps") or []:
        rows.append(
            "<article class='graph-card'>"
            f"<h3>{e(Path(minimap.get('source_video') or minimap.get('video_id') or '').name)}</h3>"
            f"{_mini_bar(minimap.get('severity_bands') or [])}"
            f"<p>{e(minimap.get('segment_count'))} segments / recommendation density {e(minimap.get('recommendation_density'))}</p>"
            f"<a class='more-link' href='enhanced_video_timeline_{e(minimap.get('video_id'))}.html'>Open enhanced timeline</a>"
            "</article>"
        )
    body = panel("Limitation", LIMITATION) + "<section class='graph-card-grid'>" + "".join(rows) + "</section>"
    return _workstation_page("Enhanced Corpus Timeline Overview", "Timeline Workstation", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links], depth="timeline")


def render_timeline_minimap_page(minimap: dict, links: list[tuple[str, str]]) -> str:
    body = panel("Limitation", LIMITATION) + f"<section class='panel'><h2>Severity Minimap</h2>{_mini_bar(minimap.get('severity_bands') or [])}</section>" + panel("High Priority Regions", [row.get("segment_id") for row in minimap.get("high_priority_regions") or []] or ["No high-priority regions."])
    return _workstation_page(f"Timeline Minimap {minimap.get('video_id')}", "Minimap", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links], depth="timeline")


def render_overlay_lane_view(lanes: list[dict], video_id: str, links: list[tuple[str, str]]) -> str:
    body = panel("Limitation", LIMITATION) + "<section class='panel'><h2>Overlay Lane Groups</h2>" + "".join(f"<details class='overlay-lane' open><summary>{e(row.get('lane_label'))} ({e(row.get('overlay_count'))})</summary><p>{e(row.get('explanation'))}</p></details>" for row in lanes) + "</section>"
    return _workstation_page(f"Overlay Lane View {video_id}", "Overlay Lanes", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links], depth="timeline")


def render_timeline_heatmap_page(heatmap: dict, links: list[tuple[str, str]]) -> str:
    cells = "".join(f"<div class='heatmap-cell {e(row.get('severity'))}' title='{e(row.get('segment_id'))}'><span>{e(row.get('segment_id'))}</span><small>{e(row.get('evidence_density'))}</small></div>" for row in heatmap.get("cells") or [])
    body = panel("Limitation", LIMITATION) + f"<section class='panel'><h2>Severity / Evidence Heatmap</h2><div class='heatmap-grid'>{cells}</div><p class='muted'>What this means: cell intensity is a deterministic review signal, not a causal claim.</p></section>"
    return _workstation_page(f"Timeline Heatmap {heatmap.get('video_id')}", "Temporal Heatmap", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links], depth="timeline")


def render_workstation_index(outputs: dict, links: list[tuple[str, str]]) -> str:
    manifest = outputs.get("workstation_manifest") or {}
    cards = [
        ("Timeline workstation overview", "timeline_workstation_overview.html"),
        ("Overlay filter console", "overlay_filter_console.html"),
        ("Temporal heatmaps", "temporal_heatmap_index.html"),
        ("Review flow shortcuts", "review_flow_shortcuts.html"),
        ("Review state summary", "review_state_summary.html"),
        ("Compare readability", "compare_readability_index.html"),
        ("Review session memory", "../review/review_session_dashboard.html"),
        ("Reviewer annotations", "../review/reviewer_annotations.html"),
        ("Resume review", "../review/review_resume_dashboard.html"),
        ("Operational queues", "../review/review_queue_dashboard.html"),
        ("Printable packets", "../review/printable_review_packet_index.html"),
    ]
    body = panel("Limitation", LIMITATION) + panel("Workflow Path", " -> ".join(manifest.get("workflow_path") or [])) + "<section class='link-grid'>" + "".join(f"<a href='{href}'>{label}</a>" for label, href in cards) + "</section>"
    return _workstation_page("Timeline Workstation", "Advanced Review Workstation", "workstation_index.html", body, [(label, f"../{href}") for label, href in links])


def render_timeline_workstation_overview(outputs: dict, links: list[tuple[str, str]]) -> str:
    rows = "".join(f"<article class='graph-card'><h3>{e(row.get('video_id'))}</h3><p>{e(row.get('segment_count'))} segments</p><a class='more-link' href='../timeline/enhanced_video_timeline_{e(row.get('video_id'))}.html'>Open enhanced timeline</a></article>" for row in (outputs.get("timeline_minimap_registry") or {}).get("minimaps") or [])
    body = panel("Limitation", LIMITATION) + panel("What This Means", "Use this page to choose the next timeline region to review. Signals are directional editorial heuristics.") + "<section class='graph-card-grid'>" + rows + "</section>"
    return _workstation_page("Timeline Workstation Overview", "Workstation Overview", "timeline_workstation_overview.html", body, [(label, f"../{href}") for label, href in links])


def render_overlay_filter_console(outputs: dict, links: list[tuple[str, str]]) -> str:
    items = (outputs.get("overlay_filter_registry") or {}).get("filter_items") or []
    rows = "".join(f"<tr data-severity='{e(row.get('severity'))}' data-type='{e(row.get('overlay_type'))}'><td>{e(row.get('overlay_id'))}</td><td>{e(row.get('video_id'))}</td><td>{e(row.get('segment_id'))}</td><td>{_severity_badge(row.get('severity'))}</td><td>{e(row.get('overlay_type'))}</td></tr>" for row in items)
    script = """<script>
function wsFilter(mode){document.querySelectorAll('tbody tr').forEach(function(r){var show=true;if(mode==='high')show=r.dataset.severity==='high';if(mode==='rec')show=r.dataset.type==='recommendation_overlay';if(mode==='block')show=r.dataset.type==='blocker_overlay';r.hidden=!show;});}
</script>"""
    body = panel("Limitation", LIMITATION) + "<section class='panel'><h2>Overlay Filters</h2><div class='button-row'><button onclick=\"wsFilter('all')\">Toggle all</button><button onclick=\"wsFilter('high')\">High severity</button><button onclick=\"wsFilter('rec')\">Recommendations</button><button onclick=\"wsFilter('block')\">Blockers</button><button onclick=\"wsFilter('all')\">Reset</button></div><table><thead><tr><th>Overlay</th><th>Video</th><th>Segment</th><th>Severity</th><th>Type</th></tr></thead><tbody>" + rows + "</tbody></table></section>" + script
    return _workstation_page("Overlay Filter Console", "Overlay Filtering", "overlay_filter_console.html", body, [(label, f"../{href}") for label, href in links])


def render_review_flow_shortcuts_page(outputs: dict, links: list[tuple[str, str]]) -> str:
    rows = "".join(f"<article class='graph-card'><h3>{e(row.get('label'))}</h3><p>{e(row.get('review_value'))}</p><p>{e(row.get('expected_next_action'))}</p><a class='more-link' href='{e(_rel_from_workstation(row.get('target_path')))}#{e(row.get('target_anchor'))}'>Open</a></article>" for row in (outputs.get("review_flow_shortcuts") or {}).get("shortcuts") or [])
    body = panel("Limitation", LIMITATION) + "<section class='graph-card-grid'>" + rows + "</section>"
    return _workstation_page("Review Flow Shortcuts", "Review Speed", "review_flow_shortcuts.html", body, [(label, f"../{href}") for label, href in links])


def _rel_from_workstation(path: str | None) -> str:
    if not path:
        return "#"
    if path.startswith("visualizations/workstation/"):
        return Path(path).name
    if path.startswith("visualizations/"):
        return "../" + path.split("visualizations/", 1)[1]
    return "../../" + path


def render_review_state_summary_page(outputs: dict, links: list[tuple[str, str]]) -> str:
    summary = outputs.get("review_state_summary") or {}
    metrics = "".join(f"<div class='metric'><span>{e(k.replace('_', ' '))}</span><strong>{e(summary.get(k))}</strong></div>" for k in ["total_recommendations", "high_priority_recommendations", "tier_1_blockers", "unresolved_blockers", "valid_human_decisions", "rejected_human_decisions"])
    body = panel("Limitation", LIMITATION) + f"<section class='metrics compact'>{metrics}</section>" + panel("Next Recommended Review Journey", summary.get("next_recommended_review_journey") or "")
    return _workstation_page("Review State Summary", "Operational State", "review_state_summary.html", body, [(label, f"../{href}") for label, href in links])


def render_temporal_heatmap_index(outputs: dict, links: list[tuple[str, str]]) -> str:
    rows = "".join(f"<article class='graph-card'><h3>{e(row.get('video_id'))}</h3><p>{e(len(row.get('cells') or []))} cells</p><a class='more-link' href='../timeline/timeline_heatmap_{e(row.get('video_id'))}.html'>Open heatmap</a></article>" for row in (outputs.get("temporal_heatmap_registry") or {}).get("heatmaps") or [])
    body = panel("Limitation", LIMITATION) + panel("What This Means", "Temporal heatmaps combine deterministic severity, evidence, recommendation, and blocker densities for navigation.") + "<section class='graph-card-grid'>" + rows + "</section>"
    return _workstation_page("Temporal Heatmap Index", "Heatmaps", "temporal_heatmap_index.html", body, [(label, f"../{href}") for label, href in links])


def render_compare_readability_index(outputs: dict, links: list[tuple[str, str]]) -> str:
    rows = "".join(f"<article class='graph-card'><h3>{e(row.get('left_video'))} vs {e(row.get('right_video'))}</h3><p>{e(row.get('interpretation_differences'))}</p><p>{e(row.get('optimization_implications'))}</p></article>" for row in (outputs.get("compare_readability_registry") or {}).get("compare_readability_entries") or [])
    body = panel("Limitation", LIMITATION) + panel("What This Means", "Compare pages align local review scales and show directional differences without declaring a quality ranking.") + "<section class='graph-card-grid'>" + rows + "</section>"
    return _workstation_page("Compare Readability Index", "Compare Readability", "compare_readability_index.html", body, [(label, f"../{href}") for label, href in links])
