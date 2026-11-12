"""Shared helpers for deterministic review continuity artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from dashboard_layout import e
from intelligence_common import base_artifact, num
from stability import STATUS_COMPLETE, deterministic_id

REVIEW_LIMITATION = (
    "This system provides deterministic editorial-review workflow support and audit-preserving review continuity. "
    "It does not infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous "
    "creative decisions. Human review is required."
)


def review_artifact(method: str) -> dict:
    data = base_artifact(status=STATUS_COMPLETE, method=method)
    data["limitations"] = [REVIEW_LIMITATION]
    return data


def video_id_from_source(source: str | None) -> str:
    if not source:
        return "video"
    stem = Path(source).stem.lower().replace(" ", "_").replace("-", "_")
    return "".join(ch for ch in stem if ch.isalnum() or ch == "_")[:48] or "video"


def severity_rank(value: str | None) -> int:
    return {"critical": 5, "high": 4, "medium": 3, "low": 2, "review": 1, None: 0}.get(value, 1)


def effort_score(value: str | None) -> float:
    text = str(value or "").lower()
    if "low" in text:
        return 0.25
    if "medium" in text:
        return 0.55
    if "high" in text:
        return 0.85
    return 0.5


def priority_score(severity: str | None, effort: str | None, impact: float | int | None = None) -> float:
    sev = severity_rank(severity) / 5.0
    effort_bonus = 1.0 - effort_score(effort)
    impact_value = num(impact, sev)
    return round(min(1.0, (sev * 0.5) + (effort_bonus * 0.25) + (impact_value * 0.25)), 3)


def index_by(items: list[dict], key: str) -> dict:
    return {item.get(key): item for item in items if item.get(key)}


def count_by(items: list[dict], key: str) -> dict:
    return dict(Counter(item.get(key) or "unknown" for item in items))


def simple_review_page(title: str, section: str, active: str, body: str, links: list[tuple[str, str]], depth: int = 2) -> str:
    css = "../" * depth + "static_assets/report.css"
    nav_links = "".join(f"<a class='{'active' if href == active else ''}' href='{e(href)}'>{e(label)}</a>" for label, href in links)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><link rel="stylesheet" href="{e(css)}"></head>
<body><aside class="sidebar"><div class="brand">Video Insight Bundler</div><nav>{nav_links}</nav></aside>
<main class="main expert"><header class="page-header"><p>{e(section)}</p><h1>{e(title)}</h1><p class="muted">{e(REVIEW_LIMITATION)}</p></header>{body}</main></body></html>"""


def card_grid(rows: list[dict], fields: list[str], title_field: str = "id") -> str:
    cards = []
    for row in rows:
        title = row.get(title_field) or row.get("annotation_id") or row.get("queue_id") or row.get("checkpoint_id") or row.get("packet_id") or row.get("rationale_id") or "review item"
        body = "".join(f"<p><strong>{e(field.replace('_', ' ').title())}:</strong> {e(row.get(field))}</p>" for field in fields if row.get(field) is not None)
        cards.append(f"<article class='graph-card'><h3>{e(title)}</h3>{body}</article>")
    return "<section class='graph-card-grid'>" + "".join(cards) + "</section>"


def compact_metrics(metrics: list[tuple[str, object]]) -> str:
    return "<section class='metrics compact'>" + "".join(f"<div class='metric'><span>{e(label)}</span><strong>{e(value)}</strong></div>" for label, value in metrics) + "</section>"


def stable_timestamp(seed: str) -> str:
    return f"deterministic:{seed}"
