"""Validate portable review packages for file:// offline use."""

from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse

from asset_dependency_scanner import IMAGE_EXTENSIONS, classify_file, extract_references, is_text_file, resolve_reference, split_reference
from portable_exclusion_policy import RAW_MEDIA_EXTENSIONS
from stability import utc_now_iso, write_json


def _is_local_ref(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme not in {"http", "https", "mailto", "tel", "data", "javascript"} and not value.startswith("#")


def _is_absolute_live_path(value: str) -> bool:
    raw, _suffix = split_reference(value)
    return Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute() or value.startswith("file:///")


def _is_raw_media(value: str) -> bool:
    raw, _suffix = split_reference(value)
    return (Path(raw).suffix.lower() or PureWindowsPath(raw).suffix.lower()) in RAW_MEDIA_EXTENSIONS


def _safe_resolve(path: Path, root: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return root.resolve() in [resolved, *resolved.parents]


def _image_signature_ok(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return True
    data = path.read_bytes()[:16]
    if suffix == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in {".jpg", ".jpeg"}:
        return data.startswith(b"\xff\xd8")
    if suffix == ".webp":
        return data.startswith(b"RIFF") and b"WEBP" in data
    return True


def validate_portable_package(
    package_root: Path,
    *,
    strict: bool = True,
    allow_provenance_absolute_paths: bool = True,
    raw_media_allowed: bool = False,
    export_profile: str = "review",
    zip_created: bool = False,
    zip_validated: bool = False,
    extracted_zip_validated: bool = False,
) -> dict:
    root = package_root.resolve()
    errors = []
    warnings = []
    missing_required = []
    for required in ("index.html", "PACKAGE_SUMMARY.md", "portable_package_manifest.json"):
        if not (root / required).exists():
            missing_required.append(required)
            errors.append(f"Missing required package file: {required}")

    missing_assets = []
    broken_links = []
    invalid_relative_paths = []
    absolute_live_paths = []
    remote_references = []
    raw_media_files = []
    recursive_package_files = []
    source_video_placeholders = 0
    checked_counts = {
        "html_pages_checked": 0,
        "markdown_files_checked": 0,
        "json_files_checked": 0,
        "css_files_checked": 0,
        "js_files_checked": 0,
        "images_checked": 0,
        "entrypoints_checked": 1 if (root / "index.html").exists() else 0,
    }

    if not root.exists():
        errors.append(f"Package root does not exist: {root}")
    package_files = sorted(root.rglob("*")) if root.exists() else []
    for path in package_files:
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        rel_lower = rel.lower()
        if (
            "portable_review_package/portable_review_package" in rel_lower
            or rel_lower.endswith("portable_review_package.zip")
            or ("/portable_" in f"/{rel_lower}" and (rel_lower.endswith("_package.zip") or "_package/" in rel_lower))
            or "/portable_extract_" in f"/{rel_lower}"
            or rel_lower.endswith("_portable_review_package.zip")
        ):
            recursive_package_files.append(rel)
        if suffix in {".html", ".htm"}:
            checked_counts["html_pages_checked"] += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "Source video intentionally excluded" in text or "Raw media excluded" in text:
                source_video_placeholders += 1
        elif suffix == ".md":
            checked_counts["markdown_files_checked"] += 1
        elif suffix == ".json":
            checked_counts["json_files_checked"] += 1
        elif suffix == ".css":
            checked_counts["css_files_checked"] += 1
        elif suffix == ".js":
            checked_counts["js_files_checked"] += 1
        elif suffix in IMAGE_EXTENSIONS:
            checked_counts["images_checked"] += 1
            if path.stat().st_size <= 0 or not _image_signature_ok(path):
                warnings.append(f"Image signature/size warning: {rel}")
        if suffix in RAW_MEDIA_EXTENSIONS:
            raw_media_files.append(rel)
        if not is_text_file(path) or suffix == ".json":
            continue
        if rel.startswith("validation/") or rel in {
            "portable_package_validation_report.json",
            "package_diff_report.json",
            "package_size_report.json",
            "exclusion_manifest.json",
            "manifests/asset_dependency_report.json",
            "manifests/exclusion_manifest.json",
        }:
            continue
        for ref in extract_references(path):
            value = str(ref["value"])
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https"}:
                remote_references.append({"source": rel, **ref})
                continue
            raw, _suffix = split_reference(value)
            if _is_absolute_live_path(value):
                if not allow_provenance_absolute_paths or ref.get("kind") != "absolute_path":
                    absolute_live_paths.append({"source": rel, **ref})
            if allow_provenance_absolute_paths and ref.get("kind") == "absolute_path":
                continue
            if _is_local_ref(value) and raw:
                if Path(raw).suffix.lower() in RAW_MEDIA_EXTENSIONS and not raw_media_allowed:
                    warnings.append(f"Raw media live reference replaced or should point to placeholder: {rel} -> {value}")
                resolved = resolve_reference(path, root, value)
                if not resolved:
                    broken = {"source": rel, **ref}
                    broken_links.append(broken)
                    if Path(raw).suffix.lower() in IMAGE_EXTENSIONS | {".json", ".css", ".js"}:
                        missing_assets.append(broken)
                elif not _safe_resolve(resolved, root):
                    invalid_relative_paths.append({"source": rel, "value": value, "resolved_path": str(resolved)})

    inventory = []
    for path in package_files:
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        inventory.append({"path": rel, "extension": path.suffix.lower(), "category": classify_file(root, path)})
    scan_summary = {
        "dashboard_count": sum(1 for row in inventory if row["category"] == "dashboard"),
        "html_count": sum(1 for row in inventory if row["extension"] in {".html", ".htm"}),
        "graph_count": sum(1 for row in inventory if row["category"] == "graph"),
        "png_count": sum(1 for row in inventory if row["extension"] == ".png"),
        "image_count": sum(1 for row in inventory if row["extension"] in IMAGE_EXTENSIONS),
        "json_count": sum(1 for row in inventory if row["extension"] == ".json"),
        "markdown_count": sum(1 for row in inventory if row["extension"] == ".md"),
        "schema_count": sum(1 for row in inventory if row["category"] == "schema"),
        "manifest_count": sum(1 for row in inventory if row["category"] == "manifest"),
        "validation_count": sum(1 for row in inventory if "validation" in row["path"].lower()),
        "unresolved_reference_count": len(broken_links),
    }
    manifest_entries = []
    manifest_path = root / "portable_package_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_entries = manifest.get("files") or []
        except json.JSONDecodeError:
            errors.append("portable_package_manifest.json is not valid JSON")
    checksum_missing = [entry.get("package_path") for entry in manifest_entries if not entry.get("sha256")]

    giant_boards = [
        row["path"]
        for row in inventory
        if row["extension"] in IMAGE_EXTENSIONS and any(token in row["path"].lower() for token in ("giant", "board", "storyboard", "contact_sheet", "timeline_board"))
    ]
    interpretations = [
        row["path"]
        for row in inventory
        if row["category"] == "interpretation" or "interpretation" in row["path"].lower() or "llm_interpretation" in row["path"].lower()
    ]
    enriched_sections = [
        "Expert Summary",
        "What This Measures",
        "Why It Matters",
        "How To Read This",
        "Operational Interpretation",
        "Related Evidence",
        "Related Recommendations",
        "Human Review Guidance",
        "Limitations",
    ]
    enriched_hits = 0
    html_paths = root.rglob("*.html") if root.exists() else []
    for html in html_paths:
        text = html.read_text(encoding="utf-8", errors="ignore")
        if any(section in text for section in enriched_sections):
            enriched_hits += 1
    if strict and not enriched_hits:
        warnings.append("No enriched interpretation sections were detected; source analysis may predate enrichment.")
    if raw_media_files and not raw_media_allowed:
        errors.append("Raw media files are present even though raw media was not explicitly allowed.")
    if checksum_missing:
        errors.append(f"Manifest entries missing checksums: {len(checksum_missing)}")
    if recursive_package_files:
        errors.append("Recursive portable package inclusion was detected.")

    synthesis_files = [
        "executive_synthesis_report.json",
        "critical_findings_registry.json",
        "review_priority_registry.json",
        "high_signal_artifact_registry.json",
    ]
    review_workflow_files = [
        "review_workspace_registry.json",
        "review_checklists.json",
        "review_handoff_registry.json",
        "review_progress_templates.json",
    ]
    change_files = [
        "change_intelligence_report.json",
        "longitudinal_summary_report.json",
        "trend_priority_registry.json",
        "evolution_highlights.json",
    ]
    ux_files = [
        "dashboard_consistency_validation.json",
        "artifact_reduction_report.json",
        "review_ux_registry.json",
        "information_density_registry.json",
        "dashboard_visibility_profiles.json",
    ]
    synthesis_present = all((root / rel).exists() for rel in synthesis_files)
    review_workspace_present = all((root / rel).exists() for rel in review_workflow_files)
    change_intelligence_present = all((root / rel).exists() for rel in change_files)
    progressive_disclosure_present = all((root / rel).exists() for rel in ux_files)
    index_text = (root / "index.html").read_text(encoding="utf-8", errors="ignore") if (root / "index.html").exists() else ""
    review_guidance_present = "Highest Priority Review Actions" in index_text and "Recommended Review Pathway" in index_text
    executive_summary_present = "Executive Summary" in index_text and synthesis_present
    navigation_scannability_present = "Top Findings" in index_text and "Audit Details" in index_text
    if strict and not synthesis_present:
        warnings.append("Synthesis quality files were not detected; export may predate executive synthesis.")
    if strict and not review_guidance_present:
        warnings.append("Review guidance sections were not detected in index.html.")
    if strict and not progressive_disclosure_present:
        warnings.append("Progressive disclosure and information density registries were not detected.")

    broken_link_count = len(broken_links)
    missing_asset_count = len(missing_assets)
    absolute_live_path_count = len(absolute_live_paths)
    remote_dependency_count = len(remote_references)
    unresolved_reference_count = scan_summary.get("unresolved_reference_count", 0)
    validation_passed = not errors and not broken_links and not missing_assets and not absolute_live_paths and not remote_references and not invalid_relative_paths
    report = {
        "validation_passed": validation_passed,
        "analysis_status": "complete" if validation_passed else "error",
        "method": "portable_package_validation_v2",
        "profile": export_profile,
        "generated_at_utc": utc_now_iso(),
        "package_root": root.as_posix(),
        "broken_link_count": broken_link_count,
        "missing_asset_count": missing_asset_count,
        "absolute_live_path_count": absolute_live_path_count,
        "absolute_reference_count": absolute_live_path_count,
        "remote_dependency_count": remote_dependency_count,
        "remote_reference_count": remote_dependency_count,
        "raw_media_included": bool(raw_media_files),
        "raw_media_included_count": len(raw_media_files),
        "raw_media_excluded": not raw_media_allowed,
        "raw_media_excluded_count": 0,
        "recursive_package_inclusion_detected": bool(recursive_package_files),
        "stale_artifact_warnings": [],
        "profile_policy_violations": [],
        "unreachable_suspicious_files": [],
        "privacy_warnings": [],
        "zip_created": zip_created,
        "zip_validated": zip_validated,
        "extracted_zip_validated": extracted_zip_validated,
        "unresolved_reference_count": unresolved_reference_count,
        "dashboard_consistency_present": (root / "dashboard_consistency_validation.json").exists(),
        "synthesis_quality_present": synthesis_present,
        "review_guidance_present": review_guidance_present,
        "review_workspace_generation_present": review_workspace_present,
        "handoff_generation_present": (root / "review_handoff_registry.json").exists(),
        "change_intelligence_generation_present": change_intelligence_present,
        "executive_summary_generation_present": executive_summary_present,
        "reduction_consistency_present": (root / "artifact_reduction_report.json").exists(),
        "navigation_scannability_present": navigation_scannability_present,
        "progressive_disclosure_support_present": progressive_disclosure_present,
        "orphan_required_asset_count": 0,
        "html_pages_checked": checked_counts["html_pages_checked"],
        "markdown_files_checked": checked_counts["markdown_files_checked"],
        "json_files_checked": checked_counts["json_files_checked"],
        "css_files_checked": checked_counts["css_files_checked"],
        "js_files_checked": checked_counts["js_files_checked"],
        "images_checked": checked_counts["images_checked"],
        "giant_boards_checked": len(giant_boards),
        "entrypoints_checked": checked_counts["entrypoints_checked"],
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "validation_passed": validation_passed,
            "opens_offline": validation_passed,
            "broken_link_count": broken_link_count,
            "missing_asset_count": missing_asset_count,
            "absolute_live_path_count": absolute_live_path_count,
            "absolute_reference_count": absolute_live_path_count,
            "remote_dependency_count": remote_dependency_count,
            "remote_reference_count": remote_dependency_count,
            "invalid_relative_path_count": len(invalid_relative_paths),
            "dashboard_count": scan_summary.get("dashboard_count", 0),
            "html_page_count": scan_summary.get("html_count", 0),
            "graph_count": scan_summary.get("graph_count", 0),
            "png_count": scan_summary.get("png_count", 0),
            "image_count": scan_summary.get("image_count", 0),
            "json_count": scan_summary.get("json_count", 0),
            "markdown_count": scan_summary.get("markdown_count", 0),
            "schema_count": scan_summary.get("schema_count", 0),
            "manifest_count": scan_summary.get("manifest_count", 0),
            "interpretation_artifact_count": len(interpretations),
            "validation_artifact_count": scan_summary.get("validation_count", 0),
            "dashboard_consistency_present": (root / "dashboard_consistency_validation.json").exists(),
            "synthesis_quality_present": synthesis_present,
            "review_guidance_present": review_guidance_present,
            "review_workspace_generation_present": review_workspace_present,
            "handoff_generation_present": (root / "review_handoff_registry.json").exists(),
            "change_intelligence_generation_present": change_intelligence_present,
            "executive_summary_generation_present": executive_summary_present,
            "reduction_consistency_present": (root / "artifact_reduction_report.json").exists(),
            "navigation_scannability_present": navigation_scannability_present,
            "progressive_disclosure_support_present": progressive_disclosure_present,
            "raw_media_included_count": len(raw_media_files),
            "recursive_package_inclusion_detected": bool(recursive_package_files),
            "source_video_placeholder_count": source_video_placeholders,
            "giant_board_count": len(giant_boards),
            "enriched_page_section_hit_count": enriched_hits,
        },
        "broken_links": broken_links,
        "missing_assets": missing_assets,
        "absolute_references": absolute_live_paths,
        "absolute_live_paths": absolute_live_paths,
        "remote_references": remote_references,
        "invalid_relative_paths": invalid_relative_paths,
        "raw_media_files": raw_media_files,
        "recursive_package_files": recursive_package_files,
        "giant_boards": giant_boards,
        "interpretation_artifacts": interpretations,
        "missing_required_files": missing_required,
    }
    (root / "validation").mkdir(parents=True, exist_ok=True)
    write_json(root / "portable_package_validation_report.json", report)
    write_json(root / "validation" / "portable_package_validation_report.json", report)
    return report
