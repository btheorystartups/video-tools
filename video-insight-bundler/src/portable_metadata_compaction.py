"""Consolidate byte-identical generated JSON mirrors after package generation."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path, PureWindowsPath
from urllib.parse import quote, unquote, urlparse

from asset_dependency_scanner import MD_LINK_RE, TEXT_EXTENSIONS, extract_references, resolve_reference
from incremental_export import load_previous_cache, write_cache_registry
from portable_package_size_report import sha256_file
from stability import utc_now_iso, write_json

MIRROR_DIRECTORIES = ("governance", "validation", "manifests")
MIN_MIRROR_BYTES = 64 * 1024
QUOTED_VALUE_RE = re.compile(r"(?P<quote>[\"'])(?P<value>[^\"'\r\n]+)(?P=quote)")


def _rewrite_value(value: str, path: Path, root: Path, aliases: dict[str, str], *, root_relative: bool = False) -> str:
    suffix_start = min((value.index(marker) for marker in ("?", "#") if marker in value), default=len(value))
    raw, suffix = unquote(value[:suffix_start]), value[suffix_start:]
    if urlparse(value).scheme or Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute():
        return value
    normalized = raw.replace("\\", "/")
    if Path(normalized).suffix.lower() != ".json":
        return value
    if root_relative and normalized in aliases:
        return aliases[normalized] + suffix
    local = (path.parent / normalized).resolve()
    try:
        local_rel = local.relative_to(root).as_posix()
    except ValueError:
        return value
    canonical = aliases.get(local_rel) or aliases.get(normalized.removeprefix("./"))
    if not canonical:
        return value
    relative = os.path.relpath(root / canonical, path.parent).replace("\\", "/")
    return quote(relative, safe="/._-%") + suffix


def _rewrite_json(value, path: Path, root: Path, aliases: dict[str, str], key: str = ""):
    if key.startswith(("original_", "historical_")) or "provenance" in key:
        return value
    if isinstance(value, dict):
        return {name: _rewrite_json(item, path, root, aliases, name) for name, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_json(item, path, root, aliases, key) for item in value]
    if isinstance(value, str):
        return _rewrite_value(value, path, root, aliases, root_relative=key not in {"href", "src", "url"})
    return value


def rewrite_metadata_links(root: Path, aliases: dict[str, str]) -> int:
    """Rewrite live links and package-relative indexes while preserving absolute provenance."""
    root = root.resolve()
    rewritten = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS or path.relative_to(root).as_posix() in aliases or path.name == "portable_package_manifest.json":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            updated = _rewrite_json(payload, path, root, aliases)
            if updated != payload:
                write_json(path, updated)
                rewritten += 1
        else:
            def replace(match: re.Match) -> str:
                original = match.group("value")
                updated = _rewrite_value(original, path, root, aliases)
                return match.group(0).replace(original, updated, 1)

            updated = QUOTED_VALUE_RE.sub(replace, text)
            updated = MD_LINK_RE.sub(replace, updated)
            if updated != text:
                path.write_text(updated, encoding="utf-8")
                rewritten += 1
    return rewritten


def compact_package_metadata(package_root: Path) -> dict:
    """Consolidate large same-name mirrors only; preserve unique evidence and display assets."""
    root = package_root.resolve()
    previous_path = root / "portable_metadata_compaction_report.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    mirrors = {row["original_package_path"]: row for row in previous.get("consolidated_mirrors", [])}
    aliases = {}
    for directory in MIRROR_DIRECTORIES:
        for path in sorted((root / directory).glob("*.json")):
            canonical = root / path.name
            if not canonical.is_file() or path.stat().st_size < MIN_MIRROR_BYTES:
                continue
            digest = sha256_file(path)
            if digest != sha256_file(canonical):
                continue
            # Identical bytes are insufficient if relative links resolve differently
            # in the two directories. Keep such reports as separate evidence.
            if any(
                resolve_reference(path, root, ref["value"]) != resolve_reference(canonical, root, ref["value"])
                for ref in extract_references(canonical)
                if ref.get("kind") != "absolute_path"
            ):
                continue
            rel = path.relative_to(root).as_posix()
            aliases[rel] = path.name
            mirrors[rel] = {"original_package_path": rel, "canonical_path": path.name, "removed_bytes": path.stat().st_size, "sha256_before": digest}
    cache_path = root / "export_cache_registry.json"
    cache_saved = previous.get("summary", {}).get("cache_bytes_saved", 0)
    if cache_path.exists():
        cache = load_previous_cache(root)
        graph_path = root / "artifact_change_graph.json"
        if cache and cache.get("storage_format") != "shared_artifact_records_v1" and graph_path.exists():
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            records = graph.get("artifacts", [])
            expected = {
                "artifacts_by_package_path": {row["package_path"]: row for row in records},
                "artifacts_by_source": {row["source_path"]: row for row in records if row.get("source_path")},
                "artifacts_by_identity": {row["stable_identity_key"]: row for row in records},
            }
            if all(cache.get(key) == value for key, value in expected.items()):
                before = cache_path.stat().st_size
                write_cache_registry(root, cache)
                cache_saved += before - cache_path.stat().st_size
    # Reapply historical aliases too: later index/report refreshes can recreate links.
    mirrors = {rel: row for rel, row in mirrors.items() if rel in aliases or not (root / rel).exists()}
    all_aliases = {rel: row["canonical_path"] for rel, row in mirrors.items()}
    rewritten = rewrite_metadata_links(root, all_aliases)
    for rel in aliases:
        (root / rel).unlink()
    report = {
        "analysis_status": "complete",
        "method": "portable_metadata_compaction_v1",
        "generated_at_utc": previous.get("generated_at_utc") or utc_now_iso(),
        "policy": "Shared cache records and byte-identical generated JSON mirrors; unique evidence and display assets preserved.",
        "consolidated_mirrors": list(mirrors.values()),
        "summary": {
            "consolidated_mirror_count": len(mirrors),
            "mirror_bytes_saved": sum(row["removed_bytes"] for row in mirrors.values()),
            "cache_bytes_saved": cache_saved,
            "files_rewritten_this_run": rewritten,
        },
    }
    write_json(previous_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    """Compact an existing derived package without rerunning the corpus analysis."""
    import argparse

    from portable_ci_smoke_suite import run_ci_smoke_suite
    from portable_export_package import _append_generated_manifest_entries, _reconcile_package_inventory, _refresh_manifest_file_lists, _validate_extracted_zip, _zip_snapshot, write_package_summary
    from portable_package_size_report import write_size_report
    from portable_package_validator import validate_portable_package

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--zip", action="store_true")
    parser.add_argument("--validate-extracted", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_extracted and not args.zip:
        parser.error("--validate-extracted requires --zip")
    root = args.package.resolve()
    manifest = json.loads((root / "portable_package_manifest.json").read_text(encoding="utf-8"))
    before = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    report = compact_package_metadata(root)
    _append_generated_manifest_entries(root, manifest)
    _refresh_manifest_file_lists(root, manifest)
    aliases = {row["original_package_path"]: row["canonical_path"] for row in report["consolidated_mirrors"]}
    manifest["asset_map"] = {source: aliases.get(rel, rel) for source, rel in manifest.get("asset_map", {}).items()}
    manifest["metadata_compaction_summary"] = report["summary"]
    write_json(root / "portable_package_manifest.json", manifest)
    validation = validate_portable_package(root, export_profile=manifest["export_profile"], raw_media_allowed=manifest["raw_media_included"], zip_created=args.zip)
    if not validation["validation_passed"]:
        print(json.dumps(validation, indent=2))
        return 1
    zip_path = root.with_suffix(".zip") if args.zip else None
    if (root / "portable_ci_smoke_report.json").exists():
        governance_validation = json.loads((root / "dashboard_governance_validation.json").read_text(encoding="utf-8"))
        run_ci_smoke_suite(root, validation=validation, governance_validation=governance_validation)
    exclusions = json.loads((root / "exclusion_manifest.json").read_text(encoding="utf-8"))
    privacy = json.loads((root / "validation/portable_privacy_scan_report.json").read_text(encoding="utf-8"))
    reachability = json.loads((root / "portable_reachability_report.json").read_text(encoding="utf-8"))
    source_root = Path(manifest["source_analysis_root"])
    size_report = write_size_report(root, source_root=source_root, zip_path=zip_path)
    manifest["validation_summary"] = validation["summary"]
    # Retain the published package/ZIP location when processing a staging copy.
    summary_zip = Path(manifest["zip_path"]) if manifest.get("zip_path") else zip_path
    write_package_summary(root, manifest, validation, size_report, exclusions, privacy, summary_zip, reachability)
    inventory_args = {"source_root": source_root, "zip_path": zip_path, "exclusions": exclusions.get("excluded_files", []), "max_file_size_warning_mb": 100.0}
    size_report = _reconcile_package_inventory(root, manifest, **inventory_args)
    if zip_path:
        _zip_snapshot(root, zip_path, 8)
    if args.validate_extracted:
        extracted = _validate_extracted_zip(zip_path, strict=True, allow_provenance_absolute_paths=True, raw_media_allowed=manifest["raw_media_included"], export_profile=manifest["export_profile"])
        if not extracted["validation_passed"]:
            print(json.dumps(extracted, indent=2))
            return 1
        validation["zip_validated"] = True
        validation["extracted_zip_validated"] = True
        validation["package_root"] = manifest["package_root"]
        write_json(root / "portable_package_validation_report.json", validation)
        write_json(root / "validation/portable_package_validation_report.json", validation)
        write_json(root / "validation/extracted_zip_validation_report.json", extracted)
        size_report = _reconcile_package_inventory(root, manifest, **inventory_args)
        _zip_snapshot(root, zip_path, 8)
    print(json.dumps({"package_root": str(root), "before_bytes": before, "after_bytes": manifest["total_bytes"], "zip_bytes": zip_path.stat().st_size if zip_path else None, "validation_passed": validation["validation_passed"], "extracted_zip_validated": validation["extracted_zip_validated"], "compaction": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
