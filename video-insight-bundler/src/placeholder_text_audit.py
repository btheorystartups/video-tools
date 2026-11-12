"""Audit generated dashboard HTML/Markdown for generic placeholder text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dashboard_interpretation_engine import BANNED_PLACEHOLDERS, write_json


GENERIC_PATTERNS = [
    *BANNED_PLACEHOLDERS,
    "Current Interpretation",
    "Good / Caution / Concern",
    "generic interpretation",
    "read with source page",
    "No source artifact link was available in this fixture",
    "No compact metric sample was visible on the page",
]


def severity_for(text: str) -> str:
    lower = text.lower()
    if "this restored page displays" in lower or "should be read with" in lower:
        return "critical"
    if "no source artifact" in lower or "no compact metric" in lower:
        return "high"
    if "current interpretation" in lower or "good / caution / concern" in lower:
        return "medium"
    return "low"


def audit_file(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = []
    for phrase in GENERIC_PATTERNS:
        for match in re.finditer(re.escape(phrase), text, re.I):
            findings.append(
                {
                    "file_path": str(path.resolve()),
                    "relative_path": path.relative_to(root).as_posix(),
                    "offending_text": text[max(0, match.start() - 80) : min(len(text), match.end() + 120)],
                    "matched_phrase": phrase,
                    "suggested_replacement_source": "reports/dashboard_source_mapping.json and visualizations/page_interpretations/<page>/page_interpretation.json",
                    "severity": severity_for(phrase),
                }
            )
    for match in re.finditer(r"<section[^>]*>\s*</section>|<p>\s*</p>|<li>\s*</li>", text, re.I):
        findings.append(
            {
                "file_path": str(path.resolve()),
                "relative_path": path.relative_to(root).as_posix(),
                "offending_text": match.group(0),
                "matched_phrase": "empty_html_container",
                "suggested_replacement_source": "page_interpretation.json specific_findings/evidence_sources",
                "severity": "medium",
            }
        )
    rel = path.relative_to(root).as_posix()
    is_root_page = path.parent == root / "visualizations"
    is_graph_detail = "visualizations/graph_ux/detail/" in rel
    if path.suffix.lower() == ".html" and (is_root_page or is_graph_detail) and "data-driven-interpretation:start" not in text and "page_interpretations" not in str(path):
        findings.append(
            {
                "file_path": str(path.resolve()),
                "relative_path": rel,
                "offending_text": "missing data-driven interpretation section",
                "matched_phrase": "missing_specific_values_section",
                "suggested_replacement_source": "Run dashboard_interpretation_engine.py for this output tree.",
                "severity": "high",
            }
        )
    return findings


def run(analysis_dir: Path) -> dict:
    targets = []
    vis = analysis_dir / "visualizations"
    if vis.exists():
        targets.extend(path for path in vis.rglob("*.html") if "page_interpretations" not in path.parts)
        targets.extend(path for path in vis.rglob("*.md"))
    targets.extend((analysis_dir / "reports").glob("*.md") if (analysis_dir / "reports").exists() else [])
    findings = []
    for path in sorted(set(targets), key=lambda p: str(p).lower()):
        findings.extend(audit_file(path, analysis_dir))
    report = {
        "analysis_dir": str(analysis_dir.resolve()),
        "file_count": len(set(targets)),
        "finding_count": len(findings),
        "critical_or_high_count": sum(1 for row in findings if row["severity"] in {"critical", "high"}),
        "audit_passed": not findings,
        "findings": findings,
    }
    write_json(analysis_dir / "reports" / "placeholder_text_audit_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit generated HTML/Markdown for placeholder text.")
    parser.add_argument("analysis_dir", type=Path)
    args = parser.parse_args(argv)
    report = run(args.analysis_dir)
    print(json.dumps({"audit_passed": report["audit_passed"], "finding_count": report["finding_count"]}, indent=2))
    return 0 if report["audit_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
