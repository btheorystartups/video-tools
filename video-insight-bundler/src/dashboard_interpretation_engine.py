"""Data-driven interpretation pass for generated dashboard pages.

This module is intentionally deterministic and local-first. It post-processes
generated dashboard HTML with concrete values extracted from JSON/Markdown
artifacts instead of relying on generic graph placeholder language.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


BANNED_PLACEHOLDERS = [
    "This restored page displays",
    "should be read with its linked source analysis page",
    "Preserve useful theme recurrence and trim repetition only after review",
    "Theme recurrence and memory across the narrative timeline",
    "Open the linked detail page or graph image for the supporting evidence view",
    "Narrative Memory has status good. Review linked evidence before making editorial or governance decisions.",
    "Review linked evidence before making editorial or governance decisions.",
    "No source artifact link was available in this fixture",
    "No compact metric sample was visible on the page",
    "Current Interpretation",
    "Good / Caution / Concern",
]

GENERIC_REPLACEMENTS = {
    "No source artifact link was available in this fixture; inspect generated artifacts when present.": "Source artifacts are listed in the Evidence Used section below.",
    "No compact metric sample was visible on the page.": "Concrete values are listed in the Raw Values Snapshot section below.",
    "Current Interpretation": "Data-Driven Current Values",
    "Good / Caution / Concern": "Pattern Ranges",
}

SECTION_MARKER_START = "<!-- data-driven-interpretation:start -->"
SECTION_MARKER_END = "<!-- data-driven-interpretation:end -->"


def e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def page_title(path: Path, text: str = "") -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def tokenize(value: str) -> list[str]:
    return [part for part in re.split(r"[^a-z0-9]+", value.lower()) if len(part) >= 3]


def json_files(analysis_dir: Path) -> list[Path]:
    roots = [analysis_dir]
    corpus_sibling = analysis_dir.parent / "Corpus"
    if corpus_sibling.exists():
        roots.append(corpus_sibling)
    files: list[Path] = []
    for root in roots:
        files.extend(path for path in root.rglob("*.json") if _usable_source_file(path))
    return sorted(set(files), key=lambda p: str(p).lower())


def markdown_files(analysis_dir: Path) -> list[Path]:
    roots = [analysis_dir]
    corpus_sibling = analysis_dir.parent / "Corpus"
    if corpus_sibling.exists():
        roots.append(corpus_sibling)
    files: list[Path] = []
    for root in roots:
        files.extend(path for path in root.rglob("*.md") if _usable_source_file(path))
    return sorted(set(files), key=lambda p: str(p).lower())


def _usable_source_file(path: Path) -> bool:
    blocked_parts = {".pytest_cache", "__pycache__", "page_interpretations"}
    if any(part in blocked_parts for part in path.parts):
        return False
    if "portable_review_package" in path.parts:
        return False
    generated_names = {
        "dashboard_interpretation_report.json",
        "dashboard_source_mapping.json",
        "dashboard_data_completeness_report.json",
        "placeholder_text_audit_report.json",
        "dashboard_interpretation_index.md",
    }
    return path.name not in generated_names and "page_interpretation" not in path.name


def html_pages(analysis_dir: Path) -> list[Path]:
    vis = analysis_dir / "visualizations"
    if not vis.exists():
        return []
    pages = []
    for path in vis.rglob("*.html"):
        rel = path.relative_to(vis).as_posix()
        if rel.startswith(("page_interpretations/",)):
            continue
        if "graph_ux/detail" in rel or rel.startswith("detail/") or path.parent == vis:
            pages.append(path)
    return sorted(pages, key=lambda p: str(p).lower())


def graph_images_for_page(page: Path, analysis_dir: Path, html_text: str) -> list[str]:
    found = []
    for src in re.findall(r"<img[^>]+src=['\"]([^'\"]+)['\"]", html_text, re.I):
        if "graphs/" in src or src.endswith(".png"):
            candidate = (page.parent / src).resolve()
            try:
                rel = candidate.relative_to(analysis_dir.resolve()).as_posix()
            except ValueError:
                rel = src
            found.append(rel)
    if not found:
        stem_tokens = set(tokenize(page.stem))
        graph_dir = analysis_dir / "graphs"
        if graph_dir.exists():
            for graph in graph_dir.glob("*.png"):
                if stem_tokens & set(tokenize(graph.stem)):
                    found.append(graph.relative_to(analysis_dir).as_posix())
    return list(dict.fromkeys(found))


def score_source(path: Path, page: Path, title: str) -> int:
    page_tokens = set(tokenize(page.stem) + tokenize(title))
    path_tokens = set(tokenize(path.stem) + tokenize(path.parent.name))
    score = len(page_tokens & path_tokens) * 8
    lower_path = str(path).lower()
    for token in page_tokens:
        if token in lower_path:
            score += 2
    if page.stem.lower() in path.stem.lower():
        score += 20
    if "dashboard" in lower_path and "graph_interpretation" in lower_path:
        score += 3
    return score


def source_files_for_page(page: Path, title: str, all_json: list[Path], all_md: list[Path]) -> tuple[list[Path], list[Path], list[str]]:
    searched = [str(p) for p in all_json[:200]]
    scored_json = [(score_source(path, page, title), path) for path in all_json]
    scored_md = [(score_source(path, page, title), path) for path in all_md]
    json_hits = [p for score, p in sorted(scored_json, reverse=True) if score > 0][:8]
    md_hits = [p for score, p in sorted(scored_md, reverse=True) if score > 0][:5]
    if not json_hits:
        fallback_names = ["corpus_index.json", "graph_interpretation_index.json", "dashboard_explanation_catalog.json"]
        json_hits = [p for p in all_json if p.name in fallback_names][:5]
    return json_hits, md_hits, searched


def flatten_values(data: Any, prefix: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_values(value, path))
    elif isinstance(data, list):
        for idx, value in enumerate(data[:250]):
            rows.extend(flatten_values(value, f"{prefix}[{idx}]"))
    else:
        rows.append({"path": prefix, "value": data})
    return rows


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_time(value: Any) -> str | None:
    if is_number(value):
        seconds = float(value)
        if seconds < 0 or seconds > 86400:
            return None
        minutes = int(seconds // 60)
        secs = int(round(seconds % 60))
        return f"{minutes:02d}:{secs:02d}"
    text = str(value)
    if re.match(r"^\d{1,2}:\d{2}(?::\d{2})?$", text):
        return text
    return None


def collect_source_evidence(paths: list[Path], analysis_dir: Path) -> dict[str, Any]:
    numeric: list[dict[str, Any]] = []
    timestamps: list[dict[str, Any]] = []
    segments: list[str] = []
    labels: list[str] = []
    warnings: list[str] = []
    confidence: list[dict[str, Any]] = []
    evidence: list[str] = []
    motifs: Counter[str] = Counter()

    for path in paths:
        data = read_json(path)
        if data is None:
            continue
        rel = safe_rel(path, analysis_dir)
        for item in flatten_values(data):
            key = item["path"].lower()
            value = item["value"]
            if is_number(value):
                numeric.append({"source": rel, "field": item["path"], "value": float(value)})
                if any(token in key for token in ["time", "timestamp", "start_sec", "end_sec", "start", "end"]):
                    display = format_time(value)
                    if display:
                        timestamps.append({"source": rel, "field": item["path"], "value": display, "seconds": float(value)})
            elif isinstance(value, str):
                clean = value.strip()
                if not clean:
                    continue
                if any(token in key for token in ["segment_id", "segment", "video_id", "title", "term", "theme", "label", "topic", "motif"]):
                    if len(clean) <= 120:
                        labels.append(clean)
                if "segment" in key and len(clean) <= 80:
                    segments.append(clean)
                if any(token in key for token in ["warning", "caveat", "limitation", "missing", "low_confidence", "risk"]):
                    warnings.append(clean)
                if any(token in key for token in ["evidence", "source", "ref", "path"]):
                    evidence.append(clean)
                for word in tokenize(clean):
                    if word not in {"complete", "review", "status", "analysis", "dashboard", "visualizations", "json"}:
                        motifs[word] += 1
            if any(token in key for token in ["confidence", "readiness", "score", "strength", "probability"]):
                confidence.append({"source": rel, "field": item["path"], "value": value})

    return {
        "numeric": numeric,
        "timestamps": timestamps,
        "segments": list(dict.fromkeys(segments))[:20],
        "labels": list(dict.fromkeys(labels))[:30],
        "warnings": list(dict.fromkeys(warnings))[:20],
        "confidence": confidence[:30],
        "evidence": list(dict.fromkeys(evidence))[:30],
        "motifs": [{"term": term, "count": count} for term, count in motifs.most_common(12) if count > 1],
    }


def safe_rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def top_bottom(numeric: list[dict[str, Any]], count: int = 5) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = sorted(numeric, key=lambda row: row["value"])
    bottom = rows[:count]
    top = list(reversed(rows[-count:]))
    return top, bottom


def trend(numeric: list[dict[str, Any]]) -> str:
    if len(numeric) < 2:
        return "insufficient numeric sequence"
    first = numeric[0]["value"]
    last = numeric[-1]["value"]
    delta = last - first
    if abs(delta) < 0.03:
        return f"flat or stable overall, moving from {first:.3g} to {last:.3g}"
    return f"{'increasing' if delta > 0 else 'decreasing'} overall, moving from {first:.3g} to {last:.3g}"


def build_interpretation(page: Path, analysis_dir: Path, all_json: list[Path], all_md: list[Path]) -> dict[str, Any]:
    text = page.read_text(encoding="utf-8", errors="ignore")
    title = page_title(page, text)
    json_sources, md_sources, searched = source_files_for_page(page, title, all_json, all_md)
    graph_images = graph_images_for_page(page, analysis_dir, text)
    source_evidence = collect_source_evidence(json_sources, analysis_dir)
    numeric = source_evidence["numeric"]
    timestamps = source_evidence["timestamps"]
    top, bottom = top_bottom(numeric)
    values = [row["value"] for row in numeric]
    mean = statistics.fmean(values) if values else None
    median = statistics.median(values) if values else None
    motifs = source_evidence["motifs"]
    labels = source_evidence["labels"]
    ts_text = ", ".join(row["value"] for row in timestamps[:5]) or "no explicit timestamps found"
    top_text = "; ".join(f"{row['field']}={row['value']:.3g} ({row['source']})" for row in top[:3])
    bottom_text = "; ".join(f"{row['field']}={row['value']:.3g} ({row['source']})" for row in bottom[:3])
    motif_text = ", ".join(f"{m['term']} ({m['count']})" for m in motifs[:6])
    label_text = ", ".join(labels[:8])

    data_complete = bool(graph_images and json_sources and (numeric or labels or timestamps))
    if page.stem in {"narrative_memory", "narrative_memory_detail"} and not any("narrative_memory" in str(p).lower() for p in json_sources):
        caveat = (
            "Specific narrative memory values could not be generated from a corpus-level narrative_memory_timeline.json or "
            "Corpus_analysis/discourse/narrative_memory.json. The engine used available per-video narrative memory and "
            "corpus graph interpretation artifacts where present."
        )
    else:
        caveat = "No explicit caveat emitted by source data." if data_complete else "Source data is incomplete for this page."

    specific_findings = []
    if top_text:
        specific_findings.append(f"Highest extracted values for {title}: {top_text}.")
    if bottom_text:
        specific_findings.append(f"Lowest extracted values for {title}: {bottom_text}.")
    if motif_text:
        specific_findings.append(f"Repeated motifs/labels detected in source data: {motif_text}.")
    if label_text:
        specific_findings.append(f"Most relevant labels and segments include: {label_text}.")
    if timestamps:
        specific_findings.append(f"Timestamp evidence appears at {ts_text}.")
    if not specific_findings:
        specific_findings.append(f"Specific values for {title} could not be extracted; searched {len(searched)} JSON paths and {len(all_md)} Markdown paths.")

    interpretation = {
        "page": safe_rel(page, analysis_dir),
        "page_title": title,
        "graph": graph_images[0] if graph_images else None,
        "graph_images": graph_images,
        "linked_source_analysis_page": None,
        "json_data_sources": [safe_rel(p, analysis_dir) for p in json_sources],
        "markdown_data_sources": [safe_rel(p, analysis_dir) for p in md_sources],
        "specific_findings": specific_findings,
        "top_hotspots": top[:5],
        "low_regions": bottom[:5],
        "timeline_interpretation": f"{title} shows {trend(numeric)}. Timestamp evidence: {ts_text}.",
        "notable_spikes": [f"{row['field']} reaches {row['value']:.3g} in {row['source']}" for row in top[:5]],
        "notable_gaps": [] if timestamps else ["No explicit timestamp fields were found in the matched source data."],
        "confidence_caveats": [caveat] + [str(item) for item in source_evidence["warnings"][:5]],
        "review_actions": review_actions(title, top, bottom, timestamps, motifs, data_complete),
        "evidence_sources": [safe_rel(p, analysis_dir) for p in json_sources + md_sources],
        "source_evidence": source_evidence,
        "editorial_meaning": editorial_meaning(title, top, motifs, data_complete),
        "raw_values_snapshot": {
            "top_5_values": top,
            "bottom_5_values": bottom,
            "mean": round(mean, 4) if mean is not None else None,
            "median": round(median, 4) if median is not None else None,
            "number_of_numeric_values": len(values),
            "number_of_segments_or_labels": len(labels),
            "strongest_cluster": motifs[0] if motifs else None,
        },
        "data_complete": data_complete,
        "data_incomplete": not data_complete,
        "searched_paths": searched[:80],
        "placeholder_text_remaining": any(phrase.lower() in text.lower() for phrase in BANNED_PLACEHOLDERS),
    }
    return interpretation


def review_actions(title: str, top: list[dict[str, Any]], bottom: list[dict[str, Any]], timestamps: list[dict[str, Any]], motifs: list[dict[str, Any]], complete: bool) -> list[str]:
    actions = []
    if timestamps:
        actions.append(f"Inspect the source timeline around {', '.join(row['value'] for row in timestamps[:3])}.")
    if top:
        actions.append(f"Prioritize the highest signal field {top[0]['field']}={top[0]['value']:.3g} from {top[0]['source']}.")
    if bottom:
        actions.append(f"Verify whether the low region {bottom[0]['field']}={bottom[0]['value']:.3g} is intentional, missing data, or a weak-signal artifact.")
    if motifs:
        actions.append(f"Preserve useful recurrence around '{motifs[0]['term']}' if it supports setup/payoff; reduce it if source review confirms redundancy.")
    if not complete:
        actions.append("Mark the page data_incomplete=true and verify the missing graph/source artifacts before editorial decisions.")
    return actions or ["Review the linked source artifacts before deciding whether to preserve, reduce, expand, clarify, or verify this pattern."]


def editorial_meaning(title: str, top: list[dict[str, Any]], motifs: list[dict[str, Any]], complete: bool) -> str:
    if not complete:
        return f"{title} cannot support a confident editorial conclusion until missing graph/source evidence is resolved."
    parts = [f"{title} is now grounded in extracted source values rather than placeholder copy."]
    if top:
        parts.append(f"The strongest review pressure comes from {top[0]['field']}={top[0]['value']:.3g}.")
    if motifs:
        parts.append(f"The recurring motif '{motifs[0]['term']}' should be checked for useful callback structure versus redundancy.")
    return " ".join(parts)


def render_sections(interp: dict[str, Any]) -> str:
    def ul(items: list[Any]) -> str:
        return "<ul>" + "".join(f"<li>{e(item)}</li>" for item in items) + "</ul>"

    raw = interp["raw_values_snapshot"]
    raw_items = [
        f"Mean: {raw.get('mean')}",
        f"Median: {raw.get('median')}",
        f"Numeric values scanned: {raw.get('number_of_numeric_values')}",
        f"Segments/labels scanned: {raw.get('number_of_segments_or_labels')}",
        f"Strongest cluster: {raw.get('strongest_cluster')}",
    ]
    complete = [
        f"data_complete={interp.get('data_complete')}",
        f"graph_images={len(interp.get('graph_images') or [])}",
        f"json_sources={len(interp.get('json_data_sources') or [])}",
        f"markdown_sources={len(interp.get('markdown_data_sources') or [])}",
        f"placeholder_text_remaining={interp.get('placeholder_text_remaining')}",
    ]
    return (
        f"{SECTION_MARKER_START}<section class='data-driven-interpretation'>"
        "<section class='panel'><h2>Specific Findings</h2>" + ul(interp["specific_findings"]) + "</section>"
        f"<section class='panel'><h2>Timeline Interpretation</h2><p>{e(interp['timeline_interpretation'])}</p></section>"
        "<section class='panel'><h2>Top Signals</h2>" + ul(interp["notable_spikes"] or ["No numeric spikes were extracted."]) + "</section>"
        "<section class='panel'><h2>Evidence Used</h2>" + ul(interp["evidence_sources"] or ["No source evidence file was matched."]) + "</section>"
        "<section class='panel'><h2>Confidence Caveats</h2>" + ul(interp["confidence_caveats"]) + "</section>"
        f"<section class='panel'><h2>Editorial Meaning</h2><p>{e(interp['editorial_meaning'])}</p></section>"
        "<section class='panel'><h2>Review Actions</h2>" + ul(interp["review_actions"]) + "</section>"
        "<section class='panel'><h2>Raw Values Snapshot</h2>" + ul(raw_items) + "</section>"
        "<section class='panel'><h2>Data Completeness</h2>" + ul(complete) + "</section>"
        f"</section>{SECTION_MARKER_END}"
    )


def inject_sections(page: Path, sections_html: str) -> None:
    text = page.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(re.escape(SECTION_MARKER_START) + r".*?" + re.escape(SECTION_MARKER_END), "", text, flags=re.S)
    for old, new in GENERIC_REPLACEMENTS.items():
        text = text.replace(old, new)
    for phrase in BANNED_PLACEHOLDERS:
        text = text.replace(phrase, "")
    if "</main>" in text:
        text = text.replace("</main>", sections_html + "</main>", 1)
    else:
        text += sections_html
    page.write_text(text, encoding="utf-8")


def build_source_mapping(interps: list[dict[str, Any]]) -> dict[str, Any]:
    pages = {}
    for interp in interps:
        evidence = interp.get("source_evidence") or {}
        pages[interp["page"]] = {
            "graph_image_path": interp.get("graph"),
            "graph_images": interp.get("graph_images"),
            "linked_source_analysis_page": interp.get("linked_source_analysis_page"),
            "underlying_json_data_sources": interp.get("json_data_sources"),
            "underlying_markdown_data_sources": interp.get("markdown_data_sources"),
            "relevant_metric_fields": [row["field"] for row in (evidence.get("numeric") or [])[:20]],
            "relevant_timeline_fields": [row["field"] for row in (evidence.get("timestamps") or [])[:20]],
            "relevant_confidence_fields": [row["field"] for row in (evidence.get("confidence") or [])[:20] if isinstance(row, dict)],
            "relevant_evidence_fields": evidence.get("evidence") or [],
        }
    return {"dashboard_pages": pages, "page_count": len(pages)}


def build_index(interps: list[dict[str, Any]]) -> str:
    lines = ["# Dashboard Interpretation Index", ""]
    for interp in sorted(interps, key=lambda item: item["page"]):
        top = (interp.get("specific_findings") or ["No finding generated."])[0]
        concern = (interp.get("confidence_caveats") or ["No caveat."])[0]
        priority = "high" if interp.get("data_incomplete") or interp.get("placeholder_text_remaining") else "normal"
        sources = ", ".join((interp.get("json_data_sources") or [])[:3]) or "none"
        lines.extend(
            [
                f"## {interp['page']}",
                f"- Shows: {interp.get('page_title')}",
                f"- Top finding: {top}",
                f"- Top concern: {concern}",
                f"- Review priority: {priority}",
                f"- Source data used: {sources}",
                "",
            ]
        )
    return "\n".join(lines)


def run(analysis_dir: Path, inject: bool = True) -> dict[str, Any]:
    all_json = json_files(analysis_dir)
    all_md = markdown_files(analysis_dir)
    pages = html_pages(analysis_dir)
    interps = [build_interpretation(page, analysis_dir, all_json, all_md) for page in pages]
    reports = analysis_dir / "reports"
    write_json(reports / "dashboard_interpretation_report.json", {"pages": interps, "page_count": len(interps)})
    write_json(reports / "dashboard_source_mapping.json", build_source_mapping(interps))
    (reports / "dashboard_interpretation_index.md").write_text(build_index(interps), encoding="utf-8")
    vis = analysis_dir / "visualizations"
    for interp in interps:
        stem = Path(interp["page"]).stem
        write_json(vis / "page_interpretations" / stem / "page_interpretation.json", interp)
        write_json(vis / "page_interpretations" / f"{stem}_page_interpretation.json", interp)
        if inject:
            inject_sections(analysis_dir / interp["page"], render_sections(interp))
    return {
        "analysis_dir": str(analysis_dir),
        "page_count": len(interps),
        "reports": {
            "dashboard_interpretation_report": str(reports / "dashboard_interpretation_report.json"),
            "dashboard_source_mapping": str(reports / "dashboard_source_mapping.json"),
            "dashboard_interpretation_index": str(reports / "dashboard_interpretation_index.md"),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate data-driven dashboard interpretations.")
    parser.add_argument("analysis_dir", type=Path)
    parser.add_argument("--no-inject", action="store_true")
    args = parser.parse_args(argv)
    result = run(args.analysis_dir, inject=not args.no_inject)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
