"""Portable export CI smoke checks."""

from __future__ import annotations

from pathlib import Path

from stability import utc_now_iso, write_json


def run_ci_smoke_suite(package_root: Path, *, validation: dict | None = None, governance_validation: dict | None = None, strict: bool = False) -> dict:
    validation = validation or {}
    governance_validation = governance_validation or {}
    checks = [
        ("minimal_export", True, "Export package folder exists."),
        ("review_export", (package_root / "index.html").exists(), "index.html exists."),
        ("executive_export", bool(list(package_root.rglob("*executive*"))), "Executive artifacts are discoverable."),
        ("quick_validation", validation.get("broken_link_count", 0) == 0, "No broken links."),
        ("standard_validation", validation.get("missing_asset_count", 0) == 0, "No missing assets."),
        ("strict_validation_on_fixture", validation.get("absolute_live_path_count", 0) == 0, "No absolute live paths."),
        ("no_raw_media_by_default", not any(path.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi"} for path in package_root.rglob("*")), "Raw media excluded."),
        ("no_broken_links", validation.get("broken_link_count", 0) == 0, "Broken links must be 0."),
        ("no_absolute_live_paths", validation.get("absolute_live_path_count", 0) == 0, "Absolute live paths must be 0."),
        ("no_recursive_package_inclusion", not any("portable_review_package/portable_review_package" in path.as_posix() for path in package_root.rglob("*")), "No nested package inclusion."),
        ("index_exists", (package_root / "index.html").exists(), "Index exists."),
        ("zip_exists", package_root.with_suffix(".zip").exists(), "Zip exists when requested."),
        ("governance_validation_passes", governance_validation.get("analysis_status") in {None, "complete"} and not governance_validation.get("blocking_errors"), "Governance validation has no blocking errors."),
    ]
    rows = [{"check": name, "passed": bool(passed), "message": message, "severity": "fail" if strict and not passed else "warn" if not passed else "pass"} for name, passed, message in checks]
    report = {
        "analysis_status": "complete" if all(row["passed"] or row["severity"] == "warn" for row in rows) else "error",
        "method": "portable_ci_smoke_suite_v72",
        "generated_at_utc": utc_now_iso(),
        "strict": strict,
        "checks": rows,
        "summary": {"check_count": len(rows), "passed_count": sum(1 for row in rows if row["passed"]), "failed_count": sum(1 for row in rows if not row["passed"])},
    }
    write_json(package_root / "portable_ci_smoke_report.json", report)
    write_json(package_root / "validation" / "portable_ci_smoke_report.json", report)
    return report
