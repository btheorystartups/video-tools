"""Validate dashboard interpretation data completeness."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dashboard_interpretation_engine import BANNED_PLACEHOLDERS, html_pages, read_json, write_json


def page_has_specific_text(text: str) -> bool:
    return "Specific Findings" in text and bool(re.search(r"\d", text))


def evaluate_page(analysis_dir: Path, page: Path) -> dict:
    text = page.read_text(encoding="utf-8", errors="ignore")
    rel = page.relative_to(analysis_dir).as_posix()
    stem = page.stem
    interp_path = analysis_dir / "visualizations" / "page_interpretations" / stem / "page_interpretation.json"
    interp = read_json(interp_path) or {}
    graph_images = interp.get("graph_images") or []
    json_sources = interp.get("json_data_sources") or []
    md_sources = interp.get("markdown_data_sources") or []
    evidence = interp.get("source_evidence") or {}
    placeholder_hits = [phrase for phrase in BANNED_PLACEHOLDERS if phrase.lower() in text.lower()]
    return {
        "page": rel,
        "has_graph_image": bool(graph_images),
        "has_source_analysis": bool(json_sources or md_sources),
        "has_json_data": bool(json_sources),
        "has_markdown_data": bool(md_sources),
        "has_specific_interpretation": bool(interp.get("specific_findings")) and page_has_specific_text(text),
        "has_timestamps": bool(evidence.get("timestamps")),
        "has_values": bool(evidence.get("numeric")),
        "has_label_evidence": bool(evidence.get("labels") or evidence.get("motifs")),
        "has_evidence": bool(interp.get("evidence_sources")),
        "placeholder_text_remaining": bool(placeholder_hits),
        "placeholder_hits": placeholder_hits,
        "data_complete": bool(interp.get("data_complete")),
        "missing_reasons": [
            reason
            for reason, failed in [
                ("missing_graph_image", not graph_images),
                ("missing_source_analysis", not (json_sources or md_sources)),
                ("missing_specific_interpretation", not interp.get("specific_findings")),
                ("missing_evidence_references", not interp.get("evidence_sources")),
                ("placeholder_text_remaining", bool(placeholder_hits)),
            ]
            if failed
        ],
    }


def run(analysis_dir: Path) -> dict:
    entries = [evaluate_page(analysis_dir, page) for page in html_pages(analysis_dir)]
    failures = [
        row
        for row in entries
        if row["placeholder_text_remaining"]
        or not row["has_specific_interpretation"]
        or not row["has_evidence"]
        or (row["has_json_data"] and not row["has_values"] and not row["has_timestamps"] and not row["has_label_evidence"])
    ]
    report = {
        "analysis_dir": str(analysis_dir.resolve()),
        "page_count": len(entries),
        "failure_count": len(failures),
        "validation_passed": len(failures) == 0,
        "pages": entries,
        "failures": failures,
    }
    write_json(analysis_dir / "reports" / "dashboard_data_completeness_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate dashboard data completeness.")
    parser.add_argument("analysis_dir", type=Path)
    args = parser.parse_args(argv)
    report = run(args.analysis_dir)
    print(json.dumps({"validation_passed": report["validation_passed"], "failure_count": report["failure_count"]}, indent=2))
    return 0 if report["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
