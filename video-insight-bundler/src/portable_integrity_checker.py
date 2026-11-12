"""Higher-level integrity checks for portable review packages."""

from __future__ import annotations

import json
from pathlib import Path

from asset_dependency_scanner import IMAGE_EXTENSIONS, classify_file
from portable_package_validator import validate_portable_package
from stability import utc_now_iso, write_json

ENRICHED_SECTION_MARKERS = (
    "Expert Summary",
    "What This Measures",
    "Why It Matters",
    "How To Read This",
    "What The Current Values Suggest",
    "Operational Interpretation",
    "Optimization Options",
    "What To Preserve",
    "What Not To Infer",
    "Related Evidence",
    "Related Recommendations",
    "Human Review Guidance",
    "Limitations",
)


def check_portable_integrity(package_root: Path) -> dict:
    root = package_root.resolve()
    validation_path = root / "portable_package_validation_report.json"
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
    else:
        validation = validate_portable_package(root)
    inventory = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        inventory.append({"path": rel, "extension": path.suffix.lower(), "category": classify_file(root, path)})
    graph_rows = [row for row in inventory if row["category"] == "graph"]
    evidence_files = [row for row in inventory if "evidence" in row["path"].lower()]
    schema_files = [row for row in inventory if row["category"] == "schema" or "/schemas/" in f"/{row['path']}"]
    validation_files = [row for row in inventory if "validation" in row["path"].lower()]
    pages_with_interpretation = []
    pages_missing_interpretation = []
    pages_with_enriched_sections = []
    dashboards_without_css = []
    pages_without_index_route = []
    for html in sorted(root.rglob("*.html")):
        rel = html.relative_to(root).as_posix()
        text = html.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        if any(marker.lower() in lower for marker in ("interpretation", "expert summary", "how to read", "what this measures")):
            pages_with_interpretation.append(rel)
        elif html.name != "index.html":
            pages_missing_interpretation.append(rel)
        if any(marker in text for marker in ENRICHED_SECTION_MARKERS):
            pages_with_enriched_sections.append(rel)
        if html.name != "index.html" and "report.css" not in text and "<link" in lower:
            dashboards_without_css.append(rel)
        if html.name != "index.html" and "index.html" not in text and "dashboard.html" not in text:
            pages_without_index_route.append(rel)

    manifest_path = root / "portable_package_manifest.json"
    manifest_paths = set()
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_paths = {entry.get("package_path") for entry in manifest.get("files", [])}
        except json.JSONDecodeError:
            manifest_paths = set()
    validation_not_in_manifest = [row["path"] for row in validation_files if row["path"] not in manifest_paths and row["path"] != "portable_package_manifest.json"]
    schema_not_in_manifest = [row["path"] for row in schema_files if row["path"] not in manifest_paths and row["path"] != "portable_package_manifest.json"]
    image_missing = [
        item for item in validation.get("missing_assets", [])
        if Path(str(item.get("value", ""))).suffix.lower() in IMAGE_EXTENSIONS
    ]
    major_reports = [
        row["path"] for row in inventory
        if row["extension"] in {".html", ".md"} and any(token in row["path"].lower() for token in ("report", "dashboard", "index"))
    ]
    index_text = (root / "index.html").read_text(encoding="utf-8", errors="ignore") if (root / "index.html").exists() else ""
    unreachable_major_reports = [
        path for path in major_reports[:500]
        if Path(path).name not in index_text and path not in index_text and path != "index.html"
    ]
    errors = []
    if validation["summary"]["broken_link_count"]:
        errors.append("Portable validation found broken links.")
    if image_missing:
        errors.append("Portable validation found missing images.")
    if validation_not_in_manifest:
        errors.append("Validation artifacts missing from manifest entries.")
    if schema_not_in_manifest:
        errors.append("Schema artifacts missing from manifest entries.")
    report = {
        "analysis_status": "complete" if not errors else "error",
        "method": "portable_integrity_check_v2",
        "generated_at_utc": utc_now_iso(),
        "package_root": root.as_posix(),
        "summary": {
            "graph_count": len(graph_rows),
            "page_count": len(list(root.rglob("*.html"))),
            "pages_with_interpretation_count": len(pages_with_interpretation),
            "pages_missing_interpretation_count": len(pages_missing_interpretation),
            "pages_with_enriched_sections_count": len(pages_with_enriched_sections),
            "evidence_file_count": len(evidence_files),
            "schema_file_count": len(schema_files),
            "validation_file_count": len(validation_files),
            "validation_artifacts_missing_manifest_count": len(validation_not_in_manifest),
            "schema_artifacts_missing_manifest_count": len(schema_not_in_manifest),
            "dashboards_without_css_count": len(dashboards_without_css),
            "pages_without_index_route_count": len(pages_without_index_route),
            "unreachable_major_report_count": len(unreachable_major_reports),
            "broken_link_count": validation["summary"]["broken_link_count"],
            "missing_image_count": len(image_missing),
        },
        "errors": errors,
        "graphs": [row["path"] for row in graph_rows],
        "pages_with_interpretation": pages_with_interpretation,
        "pages_missing_interpretation": pages_missing_interpretation[:500],
        "pages_with_enriched_sections": pages_with_enriched_sections,
        "validation_artifacts_missing_manifest": validation_not_in_manifest[:500],
        "schema_artifacts_missing_manifest": schema_not_in_manifest[:500],
        "dashboards_without_css": dashboards_without_css[:500],
        "pages_without_index_route": pages_without_index_route[:500],
        "unreachable_major_reports": unreachable_major_reports[:500],
        "image_missing": image_missing,
    }
    (root / "validation").mkdir(parents=True, exist_ok=True)
    write_json(root / "validation" / "portable_integrity_report.json", report)
    return report
