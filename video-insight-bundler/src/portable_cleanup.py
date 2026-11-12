"""Cleanup helpers for stale portable export artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path

from stability import utc_now_iso, write_json


CLEANUP_NAMES = {
    "portable_review_package",
    "portable_package_manifest.json",
    "portable_package_validation_report.json",
    "package_diff_report.json",
    "package_size_report.json",
    "exclusion_manifest.json",
}


def find_cleanup_candidates(source_root: Path) -> list[Path]:
    root = source_root.resolve()
    candidates: list[Path] = []
    for path in root.iterdir() if root.exists() else []:
        name = path.name
        if name in CLEANUP_NAMES or name == "portable_review_package.zip":
            candidates.append(path)
        elif name.startswith("portable_extract_"):
            candidates.append(path)
        elif name.startswith("portable_") and (name.endswith("_package") or name.endswith("_package.zip")):
            candidates.append(path)
        elif name.endswith("_portable_review_package") or name.endswith("_portable_review_package.zip"):
            candidates.append(path)
    validation = root / "verification_evidence" / "portable_export_validation.json"
    if validation.exists():
        candidates.append(validation)
    return sorted(set(candidates), key=lambda item: item.as_posix().lower())


def clean_old_exports(source_root: Path, *, dry_run: bool = True) -> dict:
    root = source_root.resolve()
    candidates = find_cleanup_candidates(root)
    removed: list[str] = []
    for path in candidates:
        if dry_run:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
        removed.append(path.as_posix())
    report = {
        "analysis_status": "complete",
        "method": "portable_cleanup_v1",
        "generated_at_utc": utc_now_iso(),
        "source_root": root.as_posix(),
        "dry_run": dry_run,
        "candidate_count": len(candidates),
        "removed_count": len(removed),
        "candidates": [path.as_posix() for path in candidates],
        "removed": removed,
        "source_analysis_artifacts_deleted": False,
    }
    target = root / "portable_cleanup_report.json"
    write_json(target, report)
    return report
