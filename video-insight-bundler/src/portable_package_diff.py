"""Compare original analysis output and portable package contents."""

from __future__ import annotations

from pathlib import Path

from asset_dependency_scanner import ASSET_EXTENSIONS
from portable_exclusion_policy import RAW_MEDIA_EXTENSIONS
from stability import utc_now_iso, write_json


def write_diff_report(source_root: Path, package_root: Path, copied_map: dict[str, str], exclusions: list[dict]) -> dict:
    source_files = [
        path for path in sorted(source_root.rglob("*"))
        if path.is_file()
        and "portable_review_package" not in path.relative_to(source_root).parts
        and path.name != "portable_review_package.zip"
    ]
    copied_sources = {Path(src).resolve().as_posix(): rel for src, rel in copied_map.items()}
    exclusion_by_source = {row.get("source_path"): row for row in exclusions}
    rows = []
    unexpected_missing = []
    for path in source_files:
        src = path.resolve().as_posix()
        rel = path.relative_to(source_root).as_posix()
        exclusion = exclusion_by_source.get(src)
        if src in copied_sources:
            status = "copied"
        elif exclusion:
            rule = str(exclusion.get("matched_rule") or "")
            if path.suffix.lower() in RAW_MEDIA_EXTENSIONS:
                status = "intentionally_excluded_raw_media"
            elif "cache" in rule:
                status = "intentionally_excluded_cache"
            elif "temp" in rule:
                status = "intentionally_excluded_temp"
            else:
                status = "intentionally_excluded_unneeded"
        else:
            status = "missing_unexpected"
            if path.suffix.lower() in ASSET_EXTENSIONS:
                unexpected_missing.append(rel)
        rows.append(
            {
                "source_path": src,
                "source_relative_path": rel,
                "package_path": copied_sources.get(src),
                "classification": status,
                "important": path.suffix.lower() in ASSET_EXTENSIONS,
                "exclusion_reason": exclusion.get("reason") if exclusion else None,
            }
        )
    report = {
        "analysis_status": "complete" if not unexpected_missing else "error",
        "method": "portable_package_diff_v2",
        "generated_at_utc": utc_now_iso(),
        "summary": {
            "source_file_count": len(source_files),
            "copied_file_count": sum(1 for row in rows if row["classification"] == "copied"),
            "excluded_file_count": sum(1 for row in rows if row["classification"].startswith("intentionally_excluded")),
            "unexpected_missing_count": len(unexpected_missing),
            "unexpected_missing_important_count": len(unexpected_missing),
        },
        "files": rows,
        "unexpected_missing_important_files": unexpected_missing[:1000],
    }
    write_json(package_root / "package_diff_report.json", report)
    return report
