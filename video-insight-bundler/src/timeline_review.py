"""Timeline review page models and static HTML renderers."""

from __future__ import annotations

from pathlib import Path

from dashboard_layout import e, page, panel
from intelligence_common import base_artifact
from stability import deterministic_id
from temporal_evidence_index import LIMITATION


def build_timeline_review_index(outputs: dict, temporal_index: dict, overlays: dict, pins: dict, spikes: dict) -> dict:
    videos = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        video = videos.setdefault(entry.get("video_id"), {"video_id": entry.get("video_id"), "source_video": entry.get("source_video"), "segments": [], "duration": 0})
        video["segments"].append(entry.get("segment_id"))
        video["duration"] = max(video["duration"], entry.get("timestamp_end") or 0)
    pages = []
    for video in videos.values():
        pages.append({"video_id": video["video_id"], "source_video": video["source_video"], "duration": video["duration"], "timeline_page": f"visualizations/timeline/video_timeline_{video['video_id']}.html", "recommendation_page": f"visualizations/timeline/recommendation_timeline_{video['video_id']}.html", "segment_count": len(video["segments"])})
    output = base_artifact(method="deterministic_timeline_review_v1")
    output.update({"timeline_review_index_id": deterministic_id("TLREV", [row["video_id"] for row in pages]), "corpus_timeline_page": "visualizations/timeline/corpus_timeline_overview.html", "video_timeline_pages": pages, "overlay_registry_ref": "timeline/timeline_overlay_registry.json", "recommendation_pins_ref": "timeline/timeline_recommendation_pins.json", "metric_spikes_ref": "timeline/timeline_metric_spikes.json", "review_path": ["corpus overview", "video", "timeline", "segment", "metric spike", "recommendation", "evidence", "optimization action"], "summary": {"video_timeline_page_count": len(pages), "overlay_count": len(overlays.get("overlays") or []), "recommendation_pin_count": len(pins.get("recommendation_pins") or []), "metric_spike_count": len(spikes.get("metric_spikes") or [])}, "limitations": [LIMITATION]})
    return output


def _lane(entry: dict) -> str:
    sev = (entry.get("highest_severity_signal") or {}).get("severity") or "low"
    start = entry.get("timestamp_start") or 0
    end = entry.get("timestamp_end") or start + 1
    width = max(6, end - start)
    return f"<a class='timeline-segment {e(sev)}' style='flex:{width}' href='segment_context_{e(entry.get('video_id'))}_{e(entry.get('segment_id'))}.html'><span>{start:.2f}–{end:.2f} sec</span><small>{e(sev)} · {e(entry.get('segment_id'))}</small></a>"


def _timeline_page(html: str) -> str:
    return (
        html.replace("../static_assets/report.css", "../../static_assets/report.css")
        .replace("href='dashboard.html'", "href='../dashboard.html'")
        .replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'")
        .replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'")
        .replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")
    )


def render_timeline_review_index(data: dict, links: list[tuple[str, str]]) -> str:
    cards = "".join(f"<article class='graph-card'><h3>{e(Path(row.get('source_video') or '').name)}</h3><p>{e(row.get('segment_count'))} segments / {e(row.get('duration'))} sec</p><a class='more-link' href='timeline/{e(Path(row.get('timeline_page')).name)}'>Open timeline</a></article>" for row in data.get("video_timeline_pages") or [])
    body = panel("Review Path", " -> ".join(data.get("review_path") or [])) + f"<section class='graph-card-grid'>{cards}</section>"
    return page("Timeline Review Index", "Temporal Review", "timeline_review_index.html", body, links)


def render_corpus_timeline_overview(temporal_index: dict, links: list[tuple[str, str]]) -> str:
    by_video = {}
    for entry in temporal_index.get("temporal_evidence_entries") or []:
        by_video.setdefault(entry.get("video_id"), []).append(entry)
    rows = "".join(f"<section class='panel'><h2>{e(video)}</h2><div class='timeline-lane'>{''.join(_lane(entry) for entry in entries)}</div></section>" for video, entries in sorted(by_video.items()))
    return _timeline_page(page("Corpus Timeline Overview", "Temporal Review", "../timeline_review_index.html", rows, [(label, f"../{href}") for label, href in links]))


def render_video_timeline_page(video_page: dict, temporal_index: dict, overlays: dict, pins: dict, spikes: dict, links: list[tuple[str, str]]) -> str:
    entries = [entry for entry in temporal_index.get("temporal_evidence_entries") or [] if entry.get("video_id") == video_page.get("video_id")]
    lane = "<div class='timeline-lane'>" + "".join(_lane(entry) for entry in entries) + "</div>"
    body = panel("Limitation", LIMITATION) + lane + panel("Timeline Overlays", [row.get("overlay_type") for row in overlays.get("overlays") or [] if row.get("video_id") == video_page.get("video_id")][:20]) + panel("Recommendation Pins", [row.get("title") for row in pins.get("recommendation_pins") or [] if row.get("video_id") == video_page.get("video_id")][:20]) + panel("Metric Spikes", [row.get("metric_id") for row in spikes.get("metric_spikes") or [] if row.get("video_id") == video_page.get("video_id")][:20])
    title = Path(str(video_page.get('source_video') or '').replace('\\', '/')).name or video_page.get('video_id')
    return _timeline_page(page(f"Video Timeline: {title}", "Temporal Review", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links]))


def render_segment_context_page(panel_data: dict, links: list[tuple[str, str]]) -> str:
    body = panel("Segment Metadata", [f"{panel_data.get('source_video')}", f"{panel_data.get('segment_id')} {panel_data.get('start_time')} - {panel_data.get('end_time')}"]) + panel("Evidence Refs", panel_data.get("evidence_refs") or []) + panel("Recommendations", panel_data.get("recommendations") or []) + panel("What To Preserve", panel_data.get("what_to_preserve") or "") + panel("What To Review", panel_data.get("what_to_review") or "") + panel("What Not To Infer", panel_data.get("what_not_to_infer") or "")
    label = f"{panel_data.get('start_time', 0):.2f}–{panel_data.get('end_time', 0):.2f} sec"
    return _timeline_page(page(f"Segment Context: {label}", "Segment Context", "../timeline_review_index.html", body, [(label, f"../{href}") for label, href in links]))
