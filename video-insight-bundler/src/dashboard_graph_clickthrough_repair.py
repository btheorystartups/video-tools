"""Repair and audit actual generated dashboard graph clickthrough HTML."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

from stability import STATUS_COMPLETE, STATUS_ERROR, deterministic_id, write_json


NON_CLAIM = "This system provides deterministic editorial-review and operational workflow support. It does not infer identity, recognize faces, diagnose emotion, predict viewer behavior, or make autonomous editorial decisions. Human review is required."


CORE_GRAPHS = {
    "Emotional Arc": {
        "graph_id": "emotional_arc",
        "src": "../graphs/emotional_arc.png",
        "detail": "graph_ux/detail/emotional_arc_detail.html",
        "measures": "This graph shows deterministic editorial tone proxies over time, such as energy, valence, certainty, and intensity.",
        "why": "It is useful for reviewing tonal movement, intensity variation, recovery after intense sections, and whether delivery feels flat or appropriately consistent.",
        "read": "Read the curve as a directional editorial signal over time. It is not true emotion, facial emotion recognition, psychological diagnosis, or identity inference.",
        "good": ["Intentional variation with enough contrast to maintain interest.", "Stable reflective tone when that matches the intended style.", "Recovery after high-intensity sections."],
        "caution": ["A flat curve may be appropriate for reflective content but may need review for motivational or persuasive content.", "Abrupt jumps may be source, segmentation, or microphone artifacts."],
        "concern": ["High intensity without recovery may suggest the need for pauses, visual resets, or pacing relief."],
        "current": "Current tonal proxy evidence should be reviewed for whether stability is intentional style or a sign that the video needs more contrast.",
        "optimize": "Add pauses, visual resets, or contrast only when human review confirms the current tone underserves the editorial goal.",
        "preserve": "Preserve a flat or steady arc when the intended style is reflective, analytical, or calm.",
    },
    "Pacing Curve": {
        "graph_id": "pacing_curve",
        "src": "../graphs/pacing_curve.png",
        "detail": "graph_ux/detail/pacing_curve_detail.html",
        "measures": "This graph shows words per minute over time.",
        "why": "It helps identify rushed sections, long pauses, compressed explanation, and pacing volatility.",
        "read": "Values above the typical explanatory range may indicate rushed delivery or dense argumentation. Values below the range may reflect pauses, emphasis, segmentation artifacts, or low information density.",
        "good": ["Pace varies intentionally around emphasis and transitions.", "Dense claims have enough room for comprehension."],
        "caution": ["Fast sections can be intentional for energetic delivery.", "Slow sections can be emphasis, silence, or artifact rather than a problem."],
        "concern": ["Repeated high-compression sections around important claims deserve review."],
        "current": "Review sections outside the typical explanatory range for rushed delivery, dense argumentation, or intentional emphasis.",
        "optimize": "Add pauses, split dense sections, re-record high-compression lines, or preserve fast sections when rhetorically intentional.",
        "preserve": "Preserve energetic pacing where it supports emphasis and does not obscure meaning.",
    },
    "Acoustic Energy": {
        "graph_id": "acoustic_energy",
        "src": "../graphs/acoustic_energy_curve.png",
        "detail": "graph_ux/detail/acoustic_energy_detail.html",
        "measures": "This graph shows local RMS energy evidence over time.",
        "why": "It helps review audio dynamics, emphasis, silence, noise, and delivery intensity.",
        "read": "Spikes may represent emphasis, noise, clipping, or vocal intensity. Low sections may represent pauses, softer delivery, silence, or audio issues.",
        "good": ["Natural emphasis is visible without repeated harsh spikes.", "Low-energy regions align with intentional pauses or softer delivery."],
        "caution": ["Single spikes may be natural emphasis or noise.", "Low sections may reflect silence or segmentation artifacts."],
        "concern": ["Repeated abrupt spikes, clipping-like patterns, or unstable level changes should be checked."],
        "current": "Review energy spikes and valleys as candidate audio dynamics, noise, silence, or emphasis evidence. This does not diagnose emotion.",
        "optimize": "Check normalization, reduce abrupt spikes, preserve natural emphasis, or re-record unstable sections after review.",
        "preserve": "Preserve natural emphasis and dynamic range when it improves clarity and does not create audio artifacts.",
    },
    "Topic Timeline": {
        "graph_id": "topic_timeline",
        "src": "../graphs/topic_timeline.png",
        "detail": "graph_ux/detail/topic_timeline_detail.html",
        "measures": "This graph shows deterministic transcript-derived topic terms across segments.",
        "why": "It helps review topic progression, transitions, recurrence, and potential drift.",
        "read": "Abrupt topic changes may be intentional transitions or may require bridging language. Repeated terms may indicate thematic consistency.",
        "good": ["Topic clusters progress with clear setup, bridge, and payoff.", "Repeated terms support continuity rather than redundancy."],
        "caution": ["Deterministic term extraction may miss nuance.", "Abrupt shifts may be intentional chapter changes."],
        "concern": ["Topic jumps without bridge language can make argument flow harder to follow."],
        "current": "Review deterministic term clusters for explicit transitions, recurring themes, and possible drift.",
        "optimize": "Add transitions, clarify setup/payoff, group related concepts, or cut digressions after review.",
        "preserve": "Preserve recurring terms when they reinforce the main theme or callback structure.",
    },
}

EXTENDED_GRAPH_DETAIL_LINKS = {
    "Keyword Clusters": "topic_analysis.html",
    "Rhetorical Modes": "rhetorical_deep_dive.html",
    "Persona / Style Radar": "persona_analysis.html",
    "Transition Confidence": "segmentation_confidence.html",
    "Modality Agreement": "modality_alignment.html",
    "Discourse Flow": "discourse_state.html",
    "Argument Chains": "argument_graph.html",
    "Callback Map": "callback_resolution.html",
    "Narrative Memory": "narrative_memory.html",
    "Discourse Pressure": "discourse_state.html",
    "Ambiguity Distribution": "editorial_ambiguity.html",
    "Shot Boundary Curve": "shot_boundaries.html",
    "Visual Continuity": "visual_continuity.html",
    "Visual Boundary Alignment": "visual_boundary_alignment.html",
    "Artifact Dependency Graph": "artifact_integrity.html",
    "Graph Consistency Matrix": "graph_consistency.html",
    "Orphan Reference Map": "reference_validation.html",
    "Lineage Flow": "lineage_validation.html",
    "Dashboard Coverage": "artifact_integrity.html",
    "Semantic Readiness": "semantic_readiness.html",
    "Readiness Drift": "readiness_drift.html",
    "Metric Drift": "metric_drift.html",
    "Artifact Drift": "artifact_drift.html",
    "Dependency Drift": "run_history.html",
    "Readiness Trend": "trend_analysis.html",
    "Continuity Trend": "trend_analysis.html",
    "Contradiction Trend": "trend_analysis.html",
    "Confidence Volatility": "confidence_volatility.html",
    "Recommendation Evolution": "recommendation_evolution.html",
    "Persistent Weaknesses": "persistent_patterns.html",
    "Anomaly Clusters": "anomaly_clusters.html",
    "Discourse Evolution": "semantic_evolution.html",
    "Semantic Readiness Timeline": "semantic_evolution.html",
    "Pacing Wave Timeline": "sequence_structure.html",
    "Temporal Rhythm": "temporal_rhythm.html",
    "Narrative Phase Map": "narrative_phase_model.html",
    "Editorial Pressure": "editorial_pressure.html",
    "Contradiction Pressure": "editorial_pressure.html",
    "Recommendation Dependencies": "recommendation_dependencies.html",
    "Revision Propagation": "revision_propagation.html",
    "Structural Transitions": "sequence_structure.html",
    "Epistemic Stability": "epistemic_stability.html",
    "Creator Evolution": "creator_evolution.html",
    "Creator Stability": "creator_evolution.html",
    "Recurring Patterns": "structural_pattern_mining.html",
    "Semantic Equivalence Scaffolding": "semantic_equivalence_scaffolding.html",
}


GROUPS = [
    ("Core Analysis", "Primary graph explanations and transcript entry points.", ["Emotional Arc", "Transcript Explorer", "Segment Quality"]),
    ("Speech / Pacing", "Speaking-rate, pauses, compression, and pacing volatility.", ["Pacing", "Pacing Curve", "Transcript Density"]),
    ("Acoustic", "Audio dynamics, energy, silence, and acoustic variation.", ["Acoustic Analysis", "Acoustic Energy"]),
    ("Rhetorical / Discourse", "Topics, arguments, rhetorical structure, ambiguity, and callbacks.", ["Topic Analysis", "Topic Timeline", "Rhetorical Deep Dive", "Topic Continuity", "Rhetorical Coherence", "Discourse State", "Argument Graph", "Narrative Memory", "Callback Resolution", "Editorial Ambiguity"]),
    ("Visual", "Frame, shot, composition, and visual continuity surfaces.", ["Frame Contact Sheet", "Visual Structure", "Shot Boundaries", "Visual Continuity", "Composition Features", "Visual Boundary Alignment"]),
    ("Segment / Timeline", "Segment timelines, boundary diagnostics, and modality alignment.", ["Segment Timeline", "Segmentation Confidence", "Boundary Diagnostics", "Modality Alignment", "Continuity"]),
    ("Recommendations", "Recommendation and remediation surfaces.", ["Recommendations", "Recommendation Dependencies", "Recommendation Evolution"]),
    ("Governance / Readiness", "Readiness, mutation safety, review status, and governed release checks.", ["Release Readiness", "Mutation Safety", "Evidence Consensus"]),
    ("Operational / Validation", "Artifact, graph, reference, lineage, migration, and semantic readiness checks.", ["Artifact Integrity", "Graph Consistency", "Reference Validation", "Lineage Validation", "Migration Registry", "Semantic Readiness"]),
    ("Longitudinal / Snapshot", "Run history, drift, trend, confidence, and persistent pattern views.", ["Run History", "Artifact Drift", "Metric Drift", "Readiness Drift", "Longitudinal Analysis", "Trend Analysis", "Confidence Volatility", "Anomaly Clusters", "Persistent Patterns", "Semantic Evolution"]),
    ("Comparison", "Multi-video, style, creator, and comparative readiness views.", ["Multi-Video Analysis", "Style Fingerprints", "Rhetorical Fingerprint", "Pacing Fingerprint", "Discourse Fingerprint", "Creator Evolution", "Structural Pattern Mining", "Comparative Recommendations"]),
]


def _e(value: object) -> str:
    import html

    return html.escape("" if value is None else str(value), quote=True)


def _core_detail_html(title: str, spec: dict, analysis_dir: Path) -> str:
    graph_src = spec["src"].replace("../", "")
    graph_figure = ""
    if (analysis_dir / graph_src).exists():
        graph_figure = (
            f'<figure class="graph"><a href="../../../{_e(graph_src)}">'
            f'<img src="../../../{_e(graph_src)}" alt="{_e(title)} graph"></a>'
            f"<figcaption>{_e(title)}</figcaption></figure>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)} Detail</title><link rel="stylesheet" href="../../../static_assets/report.css"></head>
<body><main class="main expert"><header class="page-header"><p>Graph Detail</p><h1>{_e(title)}</h1><p class="muted">{_e(NON_CLAIM)}</p></header>
<p><a href="../graph_detail_index.html">Graph detail index</a> | <a href="../../dashboard.html">Dashboard</a></p>
{graph_figure}
<section class="panel"><h2>What this graph measures</h2><p>{_e(spec['measures'])}</p></section>
<section class="panel"><h2>Why it matters</h2><p>{_e(spec['why'])}</p></section>
<section class="panel"><h2>How to read it</h2><p>{_e(spec['read'])}</p></section>
<section class="panel"><h2>Good patterns</h2><ul>{''.join(f'<li>{_e(x)}</li>' for x in spec['good'])}</ul></section>
<section class="panel"><h2>Caution patterns</h2><ul>{''.join(f'<li>{_e(x)}</li>' for x in spec['caution'])}</ul></section>
<section class="panel"><h2>Concerning patterns</h2><ul>{''.join(f'<li>{_e(x)}</li>' for x in spec['concern'])}</ul></section>
<section class="panel"><h2>What the current values suggest</h2><p>{_e(spec['current'])}</p></section>
<section class="panel"><h2>Optimization options</h2><p>{_e(spec['optimize'])}</p></section>
<section class="panel"><h2>What to preserve</h2><p>{_e(spec['preserve'])}</p></section>
<section class="panel"><h2>What not to infer</h2><p>{_e(NON_CLAIM)}</p></section>
<section class="panel"><h2>Evidence and related pages</h2><p>Use the source graph image, transcript pages, recommendations, and related analysis pages before deciding on edits.</p></section>
<section class="panel"><h2>Human review notes</h2><p>These deterministic signals identify candidate review points. A human reviewer decides whether to improve, preserve, or document the pattern as intentional style.</p></section>
</main></body></html>"""


def ensure_core_detail_pages(analysis_dir: Path) -> dict:
    vis = analysis_dir / "visualizations"
    detail_dir = vis / "graph_ux" / "detail"
    detail_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for title, spec in CORE_GRAPHS.items():
        path = vis / spec["detail"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_core_detail_html(title, spec, analysis_dir), encoding="utf-8")
        written.append(str(path))
    return {"written_detail_pages": written}


def graph_detail_index_html() -> str:
    cards = []
    for title, spec in CORE_GRAPHS.items():
        cards.append(
            "<article class='graph-card'>"
            f"<h3><a href='{_e(spec['detail'].replace('graph_ux/', ''))}'>{_e(title)}</a></h3>"
            f"<p><strong>Family:</strong> Core dashboard graph</p>"
            f"<p>{_e(spec['measures'])}</p>"
            f"<p>{_e(spec['current'])}</p>"
            f"<a class='more-link' href='{_e(spec['detail'].replace('graph_ux/', ''))}'>Open detail</a>"
            "</article>"
        )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Graph Detail Index</title><link rel="stylesheet" href="../../static_assets/report.css"></head><body><main class="main expert">
<header class="page-header"><p>Graph UX</p><h1>Graph Detail Index</h1><p class="muted">{_e(NON_CLAIM)}</p></header>
<p><a href="../dashboard.html">Dashboard</a></p><section class="graph-card-grid">{''.join(cards)}</section></main></body></html>"""


def ensure_graph_detail_index(analysis_dir: Path) -> Path:
    path = analysis_dir / "visualizations" / "graph_ux" / "graph_detail_index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(graph_detail_index_html(), encoding="utf-8")
    return path


def _replace_core_graph_figure(match: re.Match) -> str:
    src = match.group("src")
    title = match.group("title")
    note = match.group("note") or ""
    spec = CORE_GRAPHS.get(title)
    if not spec:
        return match.group(0)
    detail = spec["detail"]
    note_html = f'<p class="muted">{_e(note)}</p>' if note else ""
    return (
        '<article class="graph-card graph-clickthrough-card">'
        f'<a class="graph-card-image-link" href="{_e(detail)}"><img src="{_e(src)}" alt="{_e(title)} graph"></a>'
        f'<h3><a href="{_e(detail)}">{_e(title)}</a></h3>'
        f'<p class="graph-card-subtitle">{_e(spec["measures"])}</p>'
        f'<p class="graph-card-interpretation">{_e(spec["current"])}</p>'
        f'<a class="button more-link" href="{_e(detail)}">Explain this graph</a>'
        f'{note_html}'
        '</article>'
    )


def _replace_graph_figure(match: re.Match) -> str:
    src = match.group("src")
    title = match.group("title")
    note = (match.group("note") or "").strip(" -")
    spec = CORE_GRAPHS.get(title)
    href = spec["detail"] if spec else EXTENDED_GRAPH_DETAIL_LINKS.get(title, src)
    action = "Explain this graph" if spec else "Open detail" if title in EXTENDED_GRAPH_DETAIL_LINKS else "Open graph image"
    subtitle = spec["measures"] if spec else note or "Dashboard graph evidence."
    interpretation = spec["current"] if spec else "Open the linked detail page or graph image for the supporting evidence view."
    note_html = f'<p class="muted">{_e(note)}</p>' if note else ""
    return (
        '<article class="graph-card graph-clickthrough-card">'
        f'<a class="graph-card-image-link" href="{_e(href)}"><img src="{_e(src)}" alt="{_e(title)} graph"></a>'
        f'<h3><a href="{_e(href)}">{_e(title)}</a></h3>'
        f'<p class="graph-card-subtitle">{_e(subtitle)}</p>'
        f'<p class="graph-card-interpretation">{_e(interpretation)}</p>'
        f'<a class="button more-link" href="{_e(href)}">{_e(action)}</a>'
        f"{note_html}"
        "</article>"
    )


def _replace_core_graph_article(match: re.Match) -> str:
    article = match.group(0)
    title_match = re.search(r"<h3>(?:<a[^>]*>)?(Emotional Arc|Pacing Curve|Acoustic Energy|Topic Timeline)(?:</a>)?</h3>", article, re.I)
    img_match = re.search(r"<img src=['\"](?P<src>[^'\"]+)['\"][^>]*>", article, re.I)
    if not title_match:
        return article
    title = title_match.group(1)
    spec = CORE_GRAPHS.get(title)
    if not spec:
        return article
    src = img_match.group("src") if img_match else spec["src"]
    detail = spec["detail"]
    return (
        '<article class="graph-card graph-clickthrough-card">'
        f'<a class="graph-card-image-link" href="{_e(detail)}"><img src="{_e(src)}" alt="{_e(title)} graph"></a>'
        f'<h3><a href="{_e(detail)}">{_e(title)}</a></h3>'
        f'<p class="graph-card-subtitle">{_e(spec["measures"])}</p>'
        f'<p class="graph-card-interpretation">{_e(spec["current"])}</p>'
        f'<a class="button more-link" href="{_e(detail)}">Explain this graph</a>'
        '</article>'
    )


def repair_dashboard_html(dashboard_path: Path) -> dict:
    if not dashboard_path.exists():
        return {"dashboard_path": str(dashboard_path), "repair_status": STATUS_ERROR, "reason": "missing_dashboard"}
    html = dashboard_path.read_text(encoding="utf-8")
    original = html
    figure_pattern = re.compile(
        r'<figure class="graph"><img src="(?P<src>[^"]+)" alt="(?P<title>[^"]+)"><figcaption><strong>(?P=title)</strong>(?: - (?P<note>[^<]+))?</figcaption></figure>'
    )
    html = figure_pattern.sub(_replace_graph_figure, html)
    article_pattern = re.compile(r"<article class='graph-card'>(?:(?!</article>).)*(Emotional Arc|Pacing Curve|Acoustic Energy|Topic Timeline)(?:(?!</article>).)*</article>", re.I | re.S)
    html = article_pattern.sub(_replace_core_graph_article, html)
    detail_match = re.search(r'<section class="panel"><h2>Detailed Pages</h2><div class=\'link-grid\'>(?P<links>.*?)</div></section>', html, re.S)
    if detail_match:
        detail_links = [(m.group("label"), m.group("href")) for m in re.finditer(r"<a href='(?P<href>[^']+)'>(?P<label>[^<]+)</a>", detail_match.group("links"))]
        html = html[:detail_match.start()] + f'<section class="panel"><h2>Detailed Pages</h2>{grouped_detail_links_html(detail_links)}</section>' + html[detail_match.end():]
    if "graph_ux/graph_detail_index.html" not in html and "Detailed Pages" in html:
        html = html.replace(
            '<section class="panel"><h2>Detailed Pages</h2>',
            '<section class="panel"><h2>Graph Explanation Shortcuts</h2><p><a href="graph_ux/graph_detail_index.html">Graph detail index</a></p></section><section class="panel"><h2>Detailed Pages</h2>',
        )
    if html != original:
        dashboard_path.write_text(html, encoding="utf-8")
    return {"dashboard_path": str(dashboard_path), "repair_status": STATUS_COMPLETE, "changed": html != original}


def grouped_detail_links_html(detail_links: list[tuple[str, str]]) -> str:
    link_map = {label: href for label, href in detail_links}
    used = set()
    sections = []
    for group, description, labels in GROUPS:
        items = []
        for label in labels:
            href = link_map.get(label)
            if href:
                used.add(label)
                items.append(f"<a href='{_e(href)}'>{_e(label)}</a>")
        if items:
            sections.append(f"<section class='detail-page-group'><h3>{_e(group)}</h3><p>{_e(description)}</p><div class='link-grid'>{''.join(items)}</div></section>")
    remaining = [f"<a href='{_e(href)}'>{_e(label)}</a>" for label, href in detail_links if label not in used]
    if remaining:
        sections.append(f"<section class='detail-page-group'><h3>Additional Pages</h3><p>Other generated deterministic review surfaces.</p><div class='link-grid'>{''.join(remaining)}</div></section>")
    return "<div class='detail-page-groups'>" + "".join(sections) + "</div>"


def _target_exists(base_dir: Path, href: str) -> bool:
    href = unquote(href.split("#", 1)[0])
    if not href or href.startswith(("http://", "https://", "mailto:")):
        return False
    return (base_dir / href).resolve().exists()


def _detail_checks(path: Path) -> dict:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required = [
        "What this graph measures",
        "Why it matters",
        "How to read it",
        "Good patterns",
        "Caution patterns",
        "Concerning patterns",
        "What the current values suggest",
        "Optimization options",
        "What not to infer",
    ]
    return {
        "target_page": str(path),
        "exists": path.exists(),
        "has_explanatory_text": all(item.lower() in text.lower() for item in required),
        "has_observed_value_interpretation": "What the current values suggest".lower() in text.lower(),
        "has_optimization_guidance": "Optimization options".lower() in text.lower(),
        "has_limitations": NON_CLAIM.lower() in text.lower() or "does not infer identity" in text.lower(),
        "missing_sections": [item for item in required if item.lower() not in text.lower()],
    }


def audit_dashboard_html(dashboard_path: Path) -> dict:
    text = dashboard_path.read_text(encoding="utf-8") if dashboard_path.exists() else ""
    base = dashboard_path.parent
    graph_entries = []
    for title, spec in CORE_GRAPHS.items():
        card_re = re.compile(rf'<(?:article|figure)[^>]*(?:(?!</(?:article|figure)>).)*{re.escape(title)}(?:(?!</(?:article|figure)>).)*</(?:article|figure)>', re.I | re.S)
        match = card_re.search(text)
        card = match.group(0) if match else ""
        detail = spec["detail"]
        image_link = bool(re.search(rf'<a[^>]+href=["\']{re.escape(detail)}["\'][^>]*>\s*<img', card, re.I | re.S))
        title_link = bool(re.search(rf'<h3>\s*<a[^>]+href=["\']{re.escape(detail)}["\'][^>]*>{re.escape(title)}</a>\s*</h3>', card, re.I | re.S))
        open_link = bool(re.search(rf'<a[^>]+href=["\']{re.escape(detail)}["\'][^>]*>[^<]*(Explain this graph|Open detail|More)', card, re.I | re.S))
        target_path = base / detail
        detail_result = _detail_checks(target_path)
        graph_entries.append({
            "graph_title": title,
            "card_found": bool(card),
            "image_clickable": image_link,
            "title_clickable": title_link,
            "detail_link_visible": open_link,
            "target_detail_page": detail,
            "target_page_exists": target_path.exists(),
            **detail_result,
            "status": STATUS_COMPLETE if card and image_link and title_link and open_link and detail_result["has_explanatory_text"] and detail_result["has_limitations"] else STATUS_ERROR,
        })
    grouped = "detail-page-group" in text and all(group in text for group, _, _ in GROUPS[:4])
    found = [entry for entry in graph_entries if entry["card_found"]]
    found_passed = all(entry["status"] == STATUS_COMPLETE for entry in found)
    has_all_core = len(found) == len(CORE_GRAPHS)
    return {
        "dashboard_path": str(dashboard_path),
        "contains_graph_cards": bool(found),
        "graph_cards_found": [entry["graph_title"] for entry in found],
        "graph_cards_with_links": [entry["graph_title"] for entry in graph_entries if entry["image_clickable"] and entry["title_clickable"] and entry["detail_link_visible"]],
        "graph_cards_missing_links": [entry["graph_title"] for entry in graph_entries if entry["card_found"] and not (entry["image_clickable"] and entry["title_clickable"] and entry["detail_link_visible"])],
        "graph_images_clickable": all(entry["image_clickable"] for entry in graph_entries),
        "graph_titles_clickable": all(entry["title_clickable"] for entry in graph_entries),
        "has_all_core_graph_cards": has_all_core,
        "target_detail_pages": [entry["target_detail_page"] for entry in found],
        "target_pages_exist": all(entry["target_page_exists"] for entry in found) if found else False,
        "target_pages_have_explanatory_text": all(entry["has_explanatory_text"] for entry in found) if found else False,
        "target_pages_have_observed_value_interpretation": all(entry["has_observed_value_interpretation"] for entry in found) if found else False,
        "target_pages_have_optimization_guidance": all(entry["has_optimization_guidance"] for entry in found) if found else False,
        "target_pages_have_limitations": all(entry["has_limitations"] for entry in found) if found else False,
        "detailed_pages_grid_grouped": grouped,
        "graph_detail_index_linked": "graph_ux/graph_detail_index.html" in text,
        "per_graph_results": graph_entries,
        "status": STATUS_COMPLETE if found and found_passed and ((not has_all_core) or (grouped and "graph_ux/graph_detail_index.html" in text)) else STATUS_ERROR,
    }


def _dashboard_candidates(output_dir: Path) -> list[Path]:
    candidates = [
        output_dir / "dashboard.html",
        output_dir / "corpus_dashboard.html",
        output_dir / "index.html",
        output_dir / "visualizations" / "dashboard.html",
        output_dir / "visualizations" / "corpus_dashboard.html",
    ]
    if output_dir.name == "Corpus_analysis":
        candidates.extend(output_dir.parent.glob("*_analysis/visualizations/dashboard.html"))
        candidates.extend((output_dir.parent / "Corpus").glob("*_analysis/visualizations/dashboard.html"))
    return sorted({path.resolve() for path in candidates if path.exists()})


def repair_and_audit_dashboard_clickthrough(output_dir: Path) -> dict:
    dashboards = _dashboard_candidates(output_dir)
    repair_results = []
    audits = []
    for dashboard in dashboards:
        text = dashboard.read_text(encoding="utf-8")
        if not any(title in text for title in CORE_GRAPHS):
            continue
        analysis_dir = dashboard.parent.parent
        ensure_core_detail_pages(analysis_dir)
        ensure_graph_detail_index(analysis_dir)
        repair_results.append(repair_dashboard_html(dashboard))
        audits.append(audit_dashboard_html(dashboard))
    canonical_passing = [
        row for row in audits
        if row.get("has_all_core_graph_cards")
        and row["status"] == STATUS_COMPLETE
        and row.get("graph_images_clickable")
        and row.get("graph_titles_clickable")
        and row.get("target_pages_have_explanatory_text")
        and row.get("graph_detail_index_linked")
    ]
    result = {
        "analysis_status": STATUS_COMPLETE if canonical_passing else STATUS_ERROR,
        "method": "actual_dashboard_html_graph_clickthrough_repair_v1",
        "dashboard_graph_clickthrough_audit_id": deterministic_id("DGCA", [row["dashboard_path"] for row in audits]),
        "dashboards_checked": audits,
        "repair_results": repair_results,
        "summary": {
            "dashboard_count": len(audits),
            "passing_dashboard_count": sum(1 for row in audits if row["status"] == STATUS_COMPLETE),
            "failing_dashboard_count": sum(1 for row in audits if row["status"] != STATUS_COMPLETE),
            "canonical_dashboard_files_found": len([row for row in audits if row.get("has_all_core_graph_cards")]),
            "canonical_passing_dashboard_count": len(canonical_passing),
        },
        "limitations": [NON_CLAIM],
    }
    (output_dir / "graph_ux").mkdir(parents=True, exist_ok=True)
    (output_dir / "reports").mkdir(parents=True, exist_ok=True)
    (output_dir / "verification_evidence").mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "graph_ux" / "dashboard_graph_clickthrough_audit.json", result)
    write_json(output_dir / "verification_evidence" / "dashboard_graph_clickthrough_validation.json", result)
    report = ["# Dashboard Graph Clickthrough Audit", "", f"Status: {result['analysis_status']}", "", f"Dashboards checked: {len(audits)}", ""]
    for audit in audits:
        report.extend([
            f"## {audit['dashboard_path']}",
            f"- Status: {audit['status']}",
            f"- Cards found: {', '.join(audit['graph_cards_found'])}",
            f"- Cards missing links: {', '.join(audit['graph_cards_missing_links']) or 'none'}",
            f"- Images clickable: {audit['graph_images_clickable']}",
            f"- Titles clickable: {audit['graph_titles_clickable']}",
            f"- Detail pages exist: {audit['target_pages_exist']}",
            f"- Explanatory text present: {audit['target_pages_have_explanatory_text']}",
            f"- Detailed pages grouped: {audit['detailed_pages_grid_grouped']}",
            "",
        ])
    (output_dir / "reports" / "dashboard_graph_clickthrough_audit_report.md").write_text("\n".join(report), encoding="utf-8")
    return result
