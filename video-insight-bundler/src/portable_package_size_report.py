"""Package size and large-asset reporting for portable exports."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

from portable_exclusion_policy import RAW_MEDIA_EXTENSIONS
from stability import utc_now_iso, write_json


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dir_sizes(root: Path) -> list[dict]:
    sizes = defaultdict(int)
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root)
            first = rel.parts[0] if rel.parts else "."
            sizes[first] += path.stat().st_size
    return [{"directory": key, "size_bytes": value} for key, value in sorted(sizes.items(), key=lambda item: item[1], reverse=True)]


def write_size_report(
    package_root: Path,
    *,
    source_root: Path | None = None,
    zip_path: Path | None = None,
    exclusions: list[dict] | None = None,
    max_file_size_warning_mb: float = 100.0,
) -> dict:
    files = [path for path in package_root.rglob("*") if path.is_file()]
    hashes = defaultdict(list)
    entries = []
    for path in sorted(files):
        digest = sha256_file(path)
        rel = path.relative_to(package_root).as_posix()
        size = path.stat().st_size
        hashes[digest].append(rel)
        entries.append({"path": rel, "size_bytes": size, "sha256": digest})
    original_files = [path for path in source_root.rglob("*") if path.is_file()] if source_root and source_root.exists() else []
    total = sum(row["size_bytes"] for row in entries)
    original_total = sum(path.stat().st_size for path in original_files)
    raw_media_excluded_size = sum(row.get("file_size_bytes", 0) for row in exclusions or [] if "raw_" in str(row.get("matched_rule", "")))
    huge_threshold = int(max_file_size_warning_mb * 1024 * 1024)
    giant_png_inventory = [
        row for row in entries
        if Path(row["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        and any(token in row["path"].lower() for token in ("giant", "board", "storyboard", "contact_sheet", "timeline_board", "inspection"))
    ]
    report = {
        "analysis_status": "complete",
        "method": "portable_package_size_v2",
        "generated_at_utc": utc_now_iso(),
        "summary": {
            "total_package_size_bytes": total,
            "total_size_bytes": total,
            "zip_size_bytes": zip_path.stat().st_size if zip_path and zip_path.exists() else None,
            "total_original_analysis_size_bytes": original_total,
            "size_saved_by_excluding_raw_media_bytes": raw_media_excluded_size,
            "file_count": len(entries),
            "duplicate_group_count": sum(1 for values in hashes.values() if len(values) > 1),
            "raw_media_excluded_size_bytes": raw_media_excluded_size,
            "giant_png_count": len(giant_png_inventory),
            "compressibility_estimate": round(
                sum(row["size_bytes"] for row in entries if Path(row["path"]).suffix.lower() in {".json", ".md", ".html", ".css", ".js", ".txt", ".csv", ".tsv"}) / max(total, 1),
                4,
            ),
        },
        "largest_files": sorted(entries, key=lambda row: row["size_bytes"], reverse=True)[:50],
        "largest_assets": sorted(entries, key=lambda row: row["size_bytes"], reverse=True)[:50],
        "largest_directories": _dir_sizes(package_root)[:50],
        "duplicate_files_by_hash": [{"sha256": digest, "paths": paths} for digest, paths in hashes.items() if len(paths) > 1],
        "duplicate_display_assets": [
            {"sha256": digest, "paths": paths}
            for digest, paths in hashes.items()
            if len(paths) > 1 and any(Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg", ".css", ".js"} for path in paths)
        ],
        "warnings_for_huge_display_assets": [
            row for row in entries
            if row["size_bytes"] > huge_threshold and Path(row["path"]).suffix.lower() not in RAW_MEDIA_EXTENSIONS
        ],
        "giant_png_inventory": giant_png_inventory,
    }
    write_json(package_root / "package_size_report.json", report)
    return report
