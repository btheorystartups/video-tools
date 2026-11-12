"""Safe zip modes and delta package generation for portable exports."""

from __future__ import annotations

import time
import zipfile
from pathlib import Path

from portable_package_size_report import sha256_file
from stability import utc_now_iso, write_json


def build_zip_file(package_root: Path, *, compression_level: int = 8, zip_mode: str = "full") -> tuple[Path, dict]:
    start = time.perf_counter()
    zip_path = package_root.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    compression = zipfile.ZIP_STORED if compression_level == 0 else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(zip_path, "w", compression=compression, compresslevel=compression_level if compression != zipfile.ZIP_STORED else None) as archive:
        for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
            if path.is_file():
                archive.write(path, package_root.name + "/" + path.relative_to(package_root).as_posix())
    duration = round(time.perf_counter() - start, 4)
    report = {
        "analysis_status": "complete",
        "method": "zip_assembly_v68",
        "generated_at_utc": utc_now_iso(),
        "base_package": None,
        "new_package": zip_path.resolve().as_posix(),
        "changed_files": [],
        "unchanged_files": [],
        "removed_files": [],
        "added_files": [],
        "zip_mode": zip_mode,
        "zip_duration_seconds": duration,
        "estimated_full_zip_duration_seconds": duration,
        "actual_zip_size": zip_path.stat().st_size,
        "delta_zip_size": None,
        "delta_safe_to_apply": False,
        "delta_validation_status": "not_requested",
    }
    write_json(package_root / "zip_assembly_report.json", report)
    write_json(package_root / "validation" / "zip_assembly_report.json", report)
    return zip_path, report


def _manifest_for(root: Path) -> dict[str, dict]:
    rows = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().lower()):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            rows[rel] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    return rows


def build_delta_zip(package_root: Path, base_export: Path | None, *, compression_level: int = 8) -> dict:
    base_manifest = _manifest_for(base_export) if base_export and base_export.exists() and base_export.is_dir() else {}
    current_manifest = _manifest_for(package_root)
    changed = sorted(rel for rel, row in current_manifest.items() if base_manifest.get(rel, {}).get("sha256") != row["sha256"])
    unchanged = sorted(rel for rel, row in current_manifest.items() if base_manifest.get(rel, {}).get("sha256") == row["sha256"])
    removed = sorted(rel for rel in base_manifest if rel not in current_manifest)
    delta_path = package_root.with_name(package_root.name + "_delta.zip")
    if delta_path.exists():
        delta_path.unlink()
    compression = zipfile.ZIP_STORED if compression_level == 0 else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(delta_path, "w", compression=compression, compresslevel=compression_level if compression != zipfile.ZIP_STORED else None) as archive:
        for rel in changed:
            archive.write(package_root / rel, package_root.name + "/" + rel)
        removed_manifest = package_root / "zip_delta_removed_files.json"
        write_json(removed_manifest, {"removed_files": removed})
        instructions = package_root / "zip_delta_apply_instructions.md"
        instructions.write_text(
            "# Delta Package Apply Instructions\n\n"
            "1. Start from the base portable package folder.\n"
            "2. Delete files listed in `zip_delta_removed_files.json`.\n"
            "3. Extract this delta zip over the base folder, preserving paths.\n"
            "4. Run portable package validation before review.\n",
            encoding="utf-8",
        )
        archive.write(removed_manifest, package_root.name + "/zip_delta_removed_files.json")
        archive.write(instructions, package_root.name + "/zip_delta_apply_instructions.md")
    manifest = {
        "analysis_status": "complete",
        "method": "zip_delta_manifest_v68",
        "generated_at_utc": utc_now_iso(),
        "base_package": base_export.resolve().as_posix() if base_export else None,
        "new_package": package_root.resolve().as_posix(),
        "changed_files": changed,
        "unchanged_files": unchanged,
        "removed_files": removed,
        "added_files": sorted(rel for rel in changed if rel not in base_manifest),
        "zip_mode": "delta",
        "actual_zip_size": package_root.with_suffix(".zip").stat().st_size if package_root.with_suffix(".zip").exists() else None,
        "delta_zip_path": delta_path.resolve().as_posix(),
        "delta_zip_size": delta_path.stat().st_size,
        "delta_safe_to_apply": bool(base_manifest),
        "delta_validation_status": "planned" if base_manifest else "base_export_missing_or_not_directory",
        "apply_instructions": "zip_delta_apply_instructions.md",
    }
    package_manifest = {**manifest, "validation_summary": "Delta contains changed/new files plus removed-file manifest; validate after applying."}
    write_json(package_root / "zip_delta_manifest.json", manifest)
    write_json(package_root / "export_delta_package_manifest.json", package_manifest)
    write_json(package_root / "validation" / "zip_delta_manifest.json", manifest)
    return manifest
