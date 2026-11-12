"""Scan generated analysis trees for portable-package assets and references."""

from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import unquote, urlparse

from portable_exclusion_policy import RAW_MEDIA_EXTENSIONS
from stability import utc_now_iso, write_json

TEXT_EXTENSIONS = {
    ".html",
    ".htm",
    ".md",
    ".json",
    ".css",
    ".js",
    ".txt",
    ".csv",
    ".tsv",
    ".svg",
    ".xml",
    ".yaml",
    ".yml",
}
ASSET_EXTENSIONS = TEXT_EXTENSIONS | {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".srt",
    ".pdf",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
MAX_REFERENCE_ROWS = 10000
MAX_UNRESOLVED_ROWS = 2000
MAX_REMOTE_ROWS = 2000
LIVE_REFERENCE_KEYS = {
    "href",
    "src",
    "srcset",
    "url",
    "asset",
    "assets",
    "graph",
    "graphs",
    "image",
    "images",
    "manifest",
    "dashboard",
    "report",
    "html",
    "markdown",
    "json",
    "timeline",
    "evidence",
    "schema",
    "snapshot",
    "diff",
    "replay",
}
PROVENANCE_KEYS = {
    "original_source_path",
    "original_analysis_root",
    "original_video_path",
    "original_repository_path",
    "source_video",
    "source_video_path",
    "source_path",
    "source_analysis_root",
    "source_output_dir",
    "package_root",
    "zip_path",
    "source_path_metadata",
    "source_corpus_path",
    "evidence_refs",
    "source_refs",
    "referenced_artifacts",
    "analysis_dir",
    "dependency_path",
    "path",
    "paths",
    "file",
    "files",
    "output",
    "output_dir",
    "historical_source_path",
}

HTML_ATTR_RE = re.compile(r"""(?P<attr>href|src|data-full-src|data-src)\s*=\s*["'](?P<value>[^"']+)["']""", re.I)
SRCSET_RE = re.compile(r"""(?P<attr>srcset)\s*=\s*["'](?P<value>[^"']+)["']""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*['"]?(?P<value>[^'")]+)['"]?\s*\)""", re.I)
MD_LINK_RE = re.compile(r"""(?P<bang>!?)\[[^\]]*]\((?P<value>[^)\s]+)(?:\s+"[^"]*")?\)""")
WINDOWS_ABS_RE = re.compile(r"""(?<![A-Za-z])[A-Za-z]:[\\/][^\s"'<>),]+""")
POSIX_ABS_RE = re.compile(r"""(?<![\w:])/(?:Users|home|mnt|var|tmp|opt)/[^\s"'<>),]+""")


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def normalize_rel(path: Path) -> str:
    return path.as_posix()


def is_remote_reference(value: str) -> bool:
    return urlparse(value.strip()).scheme in {"http", "https"}


def is_ignored_reference(value: str) -> bool:
    stripped = value.strip()
    if not stripped or stripped.startswith("#"):
        return True
    parsed = urlparse(stripped)
    return parsed.scheme in {"mailto", "tel", "data", "javascript"}


def is_probably_reference(value: str) -> bool:
    stripped = value.strip()
    if is_ignored_reference(stripped):
        return False
    if is_remote_reference(stripped):
        return True
    parsed = urlparse(stripped)
    if parsed.scheme and len(parsed.scheme) != 1:
        return False
    raw, _suffix = split_reference(stripped)
    suffix = Path(raw).suffix.lower() or PureWindowsPath(raw).suffix.lower()
    if suffix in ASSET_EXTENSIONS or suffix in RAW_MEDIA_EXTENSIONS:
        return True
    if "\\" in stripped:
        return True
    if "/" in stripped:
        return stripped.startswith(("./", "../", "/")) or bool(re.match(r"^[A-Za-z]:[\\/]", stripped))
    return False


def split_reference(value: str) -> tuple[str, str]:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        return value, ""
    base = value.strip()
    suffix = ""
    for marker in ("#", "?"):
        if marker in base:
            base, rest = base.split(marker, 1)
            suffix = marker + rest
            break
    return unquote(base), suffix


def discover_files(root: Path) -> list[Path]:
    ignored = {"portable_review_package", "__pycache__", ".pytest_cache", ".git", "node_modules"}
    files: list[Path] = []
    for path in root.rglob("*"):
        try:
            rel_parts = set(path.relative_to(root).parts)
        except ValueError:
            rel_parts = set(path.parts)
        if rel_parts & ignored:
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: normalize_rel(item.relative_to(root)).lower())


def _json_refs(data: Any, key_hint: str = "", key_path: str = "") -> list[dict]:
    refs: list[dict] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_text = str(key).lower()
            child_path = f"{key_path}.{key_text}" if key_path else key_text
            refs.extend(_json_refs(value, key_text, child_path))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            refs.extend(_json_refs(item, key_hint, f"{key_path}[{index}]"))
    elif isinstance(data, str):
        is_provenance = key_hint in PROVENANCE_KEYS or any(token in key_hint for token in ("original_", "provenance", "historical_"))
        key_is_live = key_hint in LIVE_REFERENCE_KEYS
        if key_is_live and not is_provenance and is_probably_reference(data):
            refs.append({"kind": "json_reference", "value": data, "json_key": key_hint, "json_path": key_path})
        if not is_provenance:
            for value in WINDOWS_ABS_RE.findall(data) + POSIX_ABS_RE.findall(data):
                refs.append({"kind": "absolute_path", "value": value, "json_key": key_hint, "json_path": key_path})
    return refs


def extract_references(path: Path) -> list[dict]:
    if not is_text_file(path):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    refs: list[dict] = []
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm", ".svg"}:
        for match in HTML_ATTR_RE.finditer(text):
            refs.append({"kind": match.group("attr").lower(), "value": match.group("value")})
        for match in SRCSET_RE.finditer(text):
            for item in match.group("value").split(","):
                refs.append({"kind": "srcset", "value": item.strip().split(" ")[0]})
    for match in CSS_URL_RE.finditer(text):
        refs.append({"kind": "css_url", "value": match.group("value")})
    if suffix == ".md":
        for match in MD_LINK_RE.finditer(text):
            refs.append({"kind": "markdown_image" if match.group("bang") else "markdown_link", "value": match.group("value")})
    if suffix == ".json":
        try:
            refs.extend(_json_refs(json.loads(text)))
        except json.JSONDecodeError:
            pass
    if suffix not in {".json"}:
        for value in WINDOWS_ABS_RE.findall(text) + POSIX_ABS_RE.findall(text):
            refs.append({"kind": "absolute_path", "value": value})
    deduped: list[dict] = []
    seen = set()
    for ref in refs:
        key = (ref.get("kind"), ref.get("value"), ref.get("json_path"))
        if key not in seen and is_probably_reference(str(ref.get("value") or "")):
            deduped.append(ref)
            seen.add(key)
    return deduped


def resolve_reference(base_file: Path, root: Path, value: str) -> Path | None:
    raw, _suffix = split_reference(value)
    if not raw or is_remote_reference(value) or is_ignored_reference(value):
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve() if candidate.exists() else None
    win_candidate = Path(PureWindowsPath(raw))
    if win_candidate.is_absolute():
        return win_candidate.resolve() if win_candidate.exists() else None
    for candidate in ((base_file.parent / raw).resolve(), (root / raw).resolve()):
        try:
            if candidate.exists():
                return candidate
        except OSError:
            continue
    suffix = Path(raw).suffix.lower() or PureWindowsPath(raw).suffix.lower()
    if Path(raw).name == raw and suffix:
        candidate_dirs: list[Path] = []
        if suffix in {".html", ".htm"}:
            candidate_dirs = [root / "visualizations", root / "visualizations" / "detail", root / "dashboards", root]
        elif suffix in IMAGE_EXTENSIONS:
            candidate_dirs = [root / "graphs", root / "images", root / "boards", root / "storyboards", root]
        elif suffix == ".css":
            candidate_dirs = [root / "static_assets", root / "assets" / "css", root]
        elif suffix == ".js":
            candidate_dirs = [root / "static_assets", root / "assets" / "js", root]
        elif suffix == ".json":
            candidate_dirs = [root / "json", root / "manifests", root]
        for directory in candidate_dirs:
            candidate = (directory / raw).resolve()
            try:
                if candidate.exists():
                    return candidate
            except OSError:
                continue
    return None


def classify_file(root: Path, path: Path) -> str:
    rel = normalize_rel(path.relative_to(root)).lower() if path.is_relative_to(root) else path.as_posix().lower()
    suffix = path.suffix.lower()
    parts = set(Path(rel).parts)
    if suffix in IMAGE_EXTENSIONS:
        if "graphs" in parts:
            return "graph"
        if any(token in rel for token in ("board", "storyboard", "contact_sheet", "inspection", "timeline", "delta")):
            return "board"
        return "image"
    if suffix in {".html", ".htm"}:
        return "dashboard" if "visualizations" in parts or "dashboard" in parts or "html" in rel else "html"
    if suffix == ".json":
        if "schema" in rel or "schemas" in parts:
            return "schema"
        if "manifest" in path.name.lower() or "manifest" in parts:
            return "manifest"
        if any(token in rel for token in ("interpretation", "llm_interpretation")):
            return "interpretation"
        if "recommendation" in rel:
            return "recommendation"
        if "evidence" in rel:
            return "evidence"
        if "governance" in rel:
            return "governance"
        if "timeline" in rel:
            return "timeline"
        if "snapshot" in rel:
            return "snapshot"
        if "diff" in rel or "delta" in rel:
            return "diff"
        if "replay" in rel:
            return "replay"
        return "json"
    if suffix == ".md":
        return "markdown"
    if suffix in {".css", ".js"}:
        return "web_asset"
    if suffix in {".csv", ".tsv"}:
        return "review_sheet"
    if any(token in rel for token in ("workflow", "timeline", "evidence", "log", "inspection", "review")):
        return "review_artifact"
    return "artifact"


def _required_flags(asset_type: str) -> tuple[bool, bool, bool]:
    display = asset_type in {"dashboard", "html", "graph", "board", "image", "web_asset"}
    analysis = asset_type in {"json", "markdown", "manifest", "schema", "interpretation", "recommendation", "evidence", "governance", "timeline", "snapshot", "diff", "replay", "review_sheet"}
    validation = asset_type in {"schema", "manifest"} or "validation" in asset_type
    return display, analysis, validation


def scan_asset_dependencies(output_dir: Path, package_root: Path | None = None, scan_references: bool = True) -> dict:
    root = output_dir.resolve()
    files = discover_files(root)
    referenced_by: dict[str, list[dict]] = {}
    inventory = []
    references = []
    reference_count = 0
    remote_reference_count = 0
    unresolved_reference_count = 0
    remote_references = []
    unresolved_references = []
    for path in files:
        rel = normalize_rel(path.relative_to(root))
        asset_type = classify_file(root, path)
        display, analysis, validation = _required_flags(asset_type)
        try:
            size_bytes = path.stat().st_size
        except FileNotFoundError:
            continue
        inventory.append(
            {
                "path": rel,
                "category": asset_type,
                "asset_type": asset_type,
                "extension": path.suffix.lower(),
                "size_bytes": size_bytes,
                "is_required_for_display": display,
                "is_required_for_analysis": analysis,
                "is_required_for_validation": validation,
            }
        )
        if not scan_references:
            continue
        for ref in extract_references(path):
            entry = {"source": rel, "referenced_by": rel, **ref}
            reference_count += 1
            if is_remote_reference(str(ref["value"])):
                remote_reference_count += 1
                if len(remote_references) < MAX_REMOTE_ROWS:
                    remote_references.append(entry)
                if len(references) < MAX_REFERENCE_ROWS:
                    references.append(entry)
                continue
            resolved = resolve_reference(path, root, str(ref["value"]))
            if resolved:
                try:
                    target_rel = normalize_rel(resolved.relative_to(root))
                    entry["resolved_relative_path"] = target_rel
                    referenced_by.setdefault(target_rel, []).append({"source": rel, "reference_type": ref["kind"], "value": ref["value"]})
                except ValueError:
                    entry["resolved_path"] = str(resolved)
                    entry["external_dependency"] = True
            elif not is_ignored_reference(str(ref["value"])):
                unresolved_reference_count += 1
                if len(unresolved_references) < MAX_UNRESOLVED_ROWS:
                    unresolved_references.append(entry)
            if len(references) < MAX_REFERENCE_ROWS:
                references.append(entry)

    dependency_rows = []
    for row in inventory:
        display, analysis, validation = row["is_required_for_display"], row["is_required_for_analysis"], row["is_required_for_validation"]
        dependency_rows.append(
            {
                "source_path": (root / row["path"]).resolve().as_posix(),
                "package_path": row["path"] if package_root else None,
                "asset_type": row["asset_type"],
                "referenced_by": referenced_by.get(row["path"], []),
                "reference_type": "inventory",
                "is_required_for_display": display,
                "is_required_for_analysis": analysis,
                "is_required_for_validation": validation,
                "copy_status": "present",
                "rewrite_status": "pending" if package_root else "not_applicable",
                "warnings": [],
            }
        )

    summary = {
        "total_files": len(inventory),
        "total_references": reference_count,
        "reference_rows_recorded": len(references),
        "remote_reference_count": remote_reference_count,
        "unresolved_reference_count": unresolved_reference_count,
        "dashboard_count": sum(1 for row in inventory if row["category"] == "dashboard"),
        "html_count": sum(1 for row in inventory if row["extension"] in {".html", ".htm"}),
        "graph_count": sum(1 for row in inventory if row["category"] == "graph"),
        "image_count": sum(1 for row in inventory if row["extension"] in IMAGE_EXTENSIONS),
        "png_count": sum(1 for row in inventory if row["extension"] == ".png"),
        "json_count": sum(1 for row in inventory if row["extension"] == ".json"),
        "markdown_count": sum(1 for row in inventory if row["extension"] == ".md"),
        "schema_count": sum(1 for row in inventory if row["category"] == "schema"),
        "manifest_count": sum(1 for row in inventory if row["category"] == "manifest"),
        "board_count": sum(1 for row in inventory if row["category"] == "board"),
        "interpretation_count": sum(1 for row in inventory if row["category"] == "interpretation"),
        "validation_count": sum(1 for row in inventory if "validation" in row["path"].lower()),
    }
    return {
        "analysis_status": "complete",
        "method": "portable_asset_dependency_scan_v2",
        "generated_at_utc": utc_now_iso(),
        "source_output_dir": root.as_posix(),
        "summary": summary,
        "inventory": inventory,
        "references": references,
        "remote_references": remote_references,
        "unresolved_references": unresolved_references,
        "asset_dependencies": dependency_rows,
    }


def write_asset_dependency_report(output_dir: Path, report_path: Path | None = None) -> dict:
    report = scan_asset_dependencies(output_dir)
    target = report_path or output_dir / "asset_dependency_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, report)
    return report
