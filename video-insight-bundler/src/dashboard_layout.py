"""Reusable static HTML helpers for expert dashboard pages."""

from __future__ import annotations

import html
import json
from pathlib import Path


DISCLAIMER = "Dashboard interpretation and optimization guidance are deterministic editorial-review aids. They do not apply edits, mutate media, infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous creative decisions. Human review is required before production or editing changes."


def e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False).replace("&", "&amp;").replace("<", "&lt;")


def badge(status: str) -> str:
    return f"<span class='badge {e(status or 'review')}'>{e(status or 'review')}</span>"


def nav(links: list[tuple[str, str]], active: str = "") -> str:
    base = [("Dashboard", "dashboard.html"), ("Graph Interpretations", "graph_interpretation_index.html"), ("Optimization", "optimization_guidance_index.html"), ("Metric Ranges", "expert_metric_ranges.html")]
    return "".join(f"<a class='{'active' if href == active else ''}' href='{e(href)}'>{e(label)}</a>" for label, href in base + links)


def page(title: str, section: str, active: str, body: str, links: list[tuple[str, str]]) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><link rel="stylesheet" href="../static_assets/report.css"></head>
<body><aside class="sidebar"><div class="brand">Video Insight Bundler</div><nav>{nav(links, active)}</nav></aside>
<main class="main expert"><header class="page-header"><p>{e(section)}</p><h1>{e(title)}</h1><p class="muted">{e(DISCLAIMER)}</p></header>{body}</main></body></html>"""


def metric_cards(metrics: list[tuple[str, object]]) -> str:
    return "<section class='metrics'>" + "".join(f"<div class='metric'><span>{e(label)}</span><strong>{e(value)}</strong></div>" for label, value in metrics) + "</section>"


def panel(title: str, items: list[str] | str, kind: str = "") -> str:
    if isinstance(items, str):
        body = f"<p>{e(items)}</p>"
    else:
        body = "<ul>" + "".join(f"<li>{e(item)}</li>" for item in items) + "</ul>"
    return f"<section class='panel {e(kind)}'><h2>{e(title)}</h2>{body}</section>"


def graph_card(interp: dict, prefix: str = "") -> str:
    detail = Path(interp.get("detail_page_path") or "").name
    return (
        "<article class='graph-card'>"
        f"<div class='card-top'><h3>{e(interp.get('graph_title'))}</h3>{badge(interp.get('status'))}</div>"
        f"<p>{e(interp.get('what_it_measures'))}</p>"
        f"<figure class='graph compact'><img src='{e(prefix)}../{e(interp.get('graph_path'))}' alt='{e(interp.get('graph_title'))}'></figure>"
        f"<p><strong>Current:</strong> {e(interp.get('current_interpretation'))}</p>"
        f"<p><strong>Action:</strong> {e('; '.join(interp.get('optimization_actions') or []))}</p>"
        f"<a class='more-link' href='detail/{e(detail)}'>More</a>"
        "</article>"
    )


def expert_index_page(title: str, section: str, active: str, summary: list[tuple[str, object]], graph_interpretations: list[dict], data: dict, links: list[tuple[str, str]]) -> str:
    body = (
        metric_cards(summary)
        + "<section class='expert-grid'><div>"
        + panel("What This Page Means", "Use this page to translate deterministic artifacts into review priorities and non-mutating optimization options.")
        + panel("What Not To Infer", ["Viewer retention, truth, intent, identity, demographics, clinical state, or actual emotion.", "Autonomous edit instructions or timeline changes."])
        + "</div><div class='graph-card-grid'>"
        + "".join(graph_card(row) for row in graph_interpretations[:8])
        + "</div></section>"
        + f"<section class='panel'><h2>Raw Artifact Preview</h2><pre>{_json(data)}</pre></section>"
    )
    return page(title, section, active, body, links)


def graph_detail_page(interp: dict, guidance: list[dict], metric_range: dict | None, links: list[tuple[str, str]]) -> str:
    actions = [row.get("recommended_action") for row in guidance if row.get("trigger_metric_or_pattern") == interp.get("metric_id")] or interp.get("optimization_actions") or []
    detail_links = [(label, href if href.startswith("../") else f"../{href}") for label, href in links]
    range_lines = []
    if metric_range:
        range_lines = [
            f"Good: {metric_range.get('good_range')}",
            f"Caution: {metric_range.get('caution_range')}",
            f"Concern: {metric_range.get('concern_range')}",
        ]
    body = (
        "<section class='expert-grid'><div>"
        + panel("What It Measures", interp.get("what_it_measures") or "")
        + panel("Why It Matters", interp.get("why_it_matters") or "")
        + panel("How To Read It", interp.get("how_to_read") or "")
        + panel("Good / Caution / Concern", range_lines or (interp.get("good_patterns") or []))
        + panel("Current Interpretation", interp.get("current_interpretation") or "")
        + panel("What Not To Infer", interp.get("what_not_to_infer") or [])
        + "</div><div>"
        + f"<figure class='graph'><img src='../../{e(interp.get('graph_path'))}' alt='{e(interp.get('graph_title'))}'><figcaption>{badge(interp.get('status'))} {e(interp.get('graph_title'))}</figcaption></figure>"
        + panel("Observed Values", _json(interp.get("current_observed_values") or {}))
        + panel("Optimization Guidance", actions)
        + panel("Evidence / References", interp.get("evidence_refs") or [])
        + "</div></section>"
    )
    return page(interp.get("graph_title") or "Graph Detail", interp.get("subsystem") or "Detail", "../graph_interpretation_index.html", body, detail_links).replace("../static_assets/report.css", "../../static_assets/report.css").replace("href='dashboard.html'", "href='../dashboard.html'").replace("href='graph_interpretation_index.html'", "href='../graph_interpretation_index.html'").replace("href='optimization_guidance_index.html'", "href='../optimization_guidance_index.html'").replace("href='expert_metric_ranges.html'", "href='../expert_metric_ranges.html'")
