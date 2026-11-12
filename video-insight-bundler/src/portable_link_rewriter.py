"""Rewrite portable-package live links to package-relative references."""

from __future__ import annotations

import json
import os
import re
from html import escape
from pathlib import Path, PureWindowsPath
from urllib.parse import quote, urlparse

from asset_dependency_scanner import CSS_URL_RE, HTML_ATTR_RE, LIVE_REFERENCE_KEYS, MD_LINK_RE, SRCSET_RE, TEXT_EXTENSIONS, PROVENANCE_KEYS, is_probably_reference, split_reference
from portable_exclusion_policy import RAW_MEDIA_EXTENSIONS
from stability import utc_now_iso, write_json

RAW_MEDIA_PLACEHOLDER = "raw_media_excluded.html"
MISSING_ASSET_PLACEHOLDER = "missing_asset_placeholder.html"
MISSING_IMAGE_PLACEHOLDER = "assets/images/missing_asset_placeholder.svg"
RAW_MEDIA_PLACEHOLDER_TEXT = (
    "Source video intentionally excluded from portable package. This package contains the derived analytical outputs, "
    "frames, graphs, reports, timelines, interpretations, and validation artifacts needed for offline review. To inspect "
    "the original media, use the source path recorded in provenance metadata on the originating machine."
)


def package_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_raw_media_reference(value: str) -> bool:
    raw, _suffix = split_reference(value)
    return (Path(raw).suffix.lower() or PureWindowsPath(raw).suffix.lower()) in RAW_MEDIA_EXTENSIONS


def _is_provenance_key(key: str) -> bool:
    key = key.lower()
    return key in PROVENANCE_KEYS or any(token in key for token in ("original_", "provenance", "historical_"))


def relative_href(from_file: Path, target: Path, package_root: Path, suffix: str = "") -> str:
    rel_target = target.resolve().relative_to(package_root.resolve())
    from_dir = from_file.parent.resolve().relative_to(package_root.resolve())
    href = os.path.relpath(package_root / rel_target, start=package_root / from_dir).replace("\\", "/")
    if not href.startswith("."):
        href = f"./{href}" if "/" not in href else href
    return quote(href, safe="/._-#?=&%") + suffix


def _mapped_target(raw: str, package_root: Path, original_root: Path, copied_map: dict[str, str]) -> Path | None:
    raw_mapped = copied_map.get(raw) or copied_map.get(raw.replace("\\", "/"))
    if raw_mapped:
        return package_root / raw_mapped
    candidate = Path(raw)
    win_candidate = Path(PureWindowsPath(raw))
    candidates = []
    if candidate.is_absolute():
        candidates.append(candidate.resolve())
    if win_candidate.is_absolute():
        candidates.append(win_candidate.resolve())
    for item in candidates:
        mapped = copied_map.get(item.resolve().as_posix()) or copied_map.get(str(item))
        if mapped:
            return package_root / mapped
        try:
            return package_root / item.relative_to(original_root.resolve())
        except ValueError:
            continue
    if candidates:
        return None
    normalized = raw.replace("\\", "/").lstrip("./")
    local = package_root / normalized
    try:
        if local.exists() and package_root.resolve() in [local.resolve(), *local.resolve().parents]:
            return local
    except OSError:
        pass
    original = (original_root / normalized).resolve()
    mapped = copied_map.get(original.as_posix()) or copied_map.get(str(original))
    if mapped:
        return package_root / mapped
    return None


def _lookup_target(value: str, source_file: Path, package_root: Path, original_root: Path, copied_map: dict[str, str]) -> tuple[Path | None, str]:
    raw, suffix = split_reference(value)
    if not raw:
        return None, suffix
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data", "javascript"}:
        return None, suffix
    mapped = _mapped_target(raw, package_root, original_root, copied_map)
    if mapped:
        return mapped, suffix
    local = (source_file.parent / raw).resolve()
    try:
        if local.exists() and package_root.resolve() in [local, *local.parents]:
            return local, suffix
        if local.exists():
            mapped = copied_map.get(local.as_posix()) or copied_map.get(str(local))
            if mapped:
                return package_root / mapped, suffix
    except OSError:
        pass
    return None, suffix


def rewrite_reference_value(
    value: str,
    source_file: Path,
    package_root: Path,
    original_root: Path,
    copied_map: dict[str, str],
    *,
    include_raw_media: bool = False,
) -> str:
    if is_raw_media_reference(value) and not include_raw_media:
        return relative_href(source_file, package_root / RAW_MEDIA_PLACEHOLDER, package_root)
    target, suffix = _lookup_target(value, source_file, package_root, original_root, copied_map)
    if not target:
        raw, _old_suffix = split_reference(value)
        suffix_lower = Path(raw).suffix.lower() or PureWindowsPath(raw).suffix.lower()
        if suffix_lower in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
            return relative_href(source_file, package_root / MISSING_IMAGE_PLACEHOLDER, package_root)
        if suffix_lower in {".html", ".htm", ".json", ".md", ".csv", ".tsv", ".txt", ".css", ".js"}:
            return relative_href(source_file, package_root / MISSING_ASSET_PLACEHOLDER, package_root)
        return value
    return relative_href(source_file, target, package_root, suffix)


def _raw_media_note() -> str:
    return f"<div class=\"raw-media-placeholder\"><strong>Raw media excluded.</strong> {RAW_MEDIA_PLACEHOLDER_TEXT}</div>"


def write_raw_media_placeholder(package_root: Path, raw_media_excluded_count: int) -> None:
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Raw Media Excluded</title><style>body{{font-family:Arial,sans-serif;margin:32px;line-height:1.5;max-width:900px}}</style></head>
<body><h1>Raw Source Media Excluded</h1><p>{RAW_MEDIA_PLACEHOLDER_TEXT}</p>
<p>Raw media files excluded: {raw_media_excluded_count}</p><p><a href="#">Back to package index when present</a></p></body></html>"""
    (package_root / RAW_MEDIA_PLACEHOLDER).write_text(html, encoding="utf-8")
    missing_html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Missing Portable Asset</title><style>body{font-family:Arial,sans-serif;margin:32px;line-height:1.5;max-width:900px}</style></head>
<body><h1>Asset Not Included</h1><p>This source reference could not be resolved into the portable package. A working placeholder is not available evidence. See validation/portable_fallback_link_audit.json for the original references and exclusion classifications where known.</p><p><a href="index.html">Return to package home</a></p></body></html>"""
    (package_root / MISSING_ASSET_PLACEHOLDER).write_text(missing_html, encoding="utf-8")
    image = """<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240">
<rect width="900" height="240" fill="#f4f4ef"/><rect x="12" y="12" width="876" height="216" fill="none" stroke="#9c4f45" stroke-width="3"/>
<text x="40" y="105" font-family="Arial, sans-serif" font-size="30" fill="#232323">Asset not included in portable package</text>
<text x="40" y="148" font-family="Arial, sans-serif" font-size="18" fill="#666a6d">See validation reports for the original unresolved reference.</text></svg>"""
    (package_root / MISSING_IMAGE_PLACEHOLDER).parent.mkdir(parents=True, exist_ok=True)
    (package_root / MISSING_IMAGE_PLACEHOLDER).write_text(image, encoding="utf-8")


def rewrite_text_links(
    text: str,
    source_file: Path,
    package_root: Path,
    original_root: Path,
    copied_map: dict[str, str],
    *,
    include_raw_media: bool = False,
) -> tuple[str, int, bool]:
    changes = 0
    raw_media_replaced = False

    def attr_replace(match: re.Match) -> str:
        nonlocal changes, raw_media_replaced
        value = match.group("value")
        replaced_media = is_raw_media_reference(value) and not include_raw_media
        rewritten = rewrite_reference_value(value, source_file, package_root, original_root, copied_map, include_raw_media=include_raw_media)
        if rewritten != value:
            changes += 1
        if replaced_media:
            raw_media_replaced = True
            return f'{match.group("attr")}="{rewritten}" data-original-source-path="{value}"'
        if rewritten != value and "missing_asset_placeholder" in rewritten:
            return f'{match.group("attr")}="{rewritten}" data-original-reference="{escape(value, quote=True)}"'
        return f'{match.group("attr")}="{rewritten}"'

    text = HTML_ATTR_RE.sub(attr_replace, text)

    def srcset_replace(match: re.Match) -> str:
        nonlocal changes
        rewritten_items = []
        for item in match.group("value").split(","):
            pieces = item.strip().split()
            if not pieces:
                continue
            new_value = rewrite_reference_value(pieces[0], source_file, package_root, original_root, copied_map, include_raw_media=include_raw_media)
            if new_value != pieces[0]:
                changes += 1
            rewritten_items.append(" ".join([new_value, *pieces[1:]]))
        return f'{match.group("attr")}="{", ".join(rewritten_items)}"'

    text = SRCSET_RE.sub(srcset_replace, text)

    def css_replace(match: re.Match) -> str:
        nonlocal changes
        value = match.group("value")
        rewritten = rewrite_reference_value(value, source_file, package_root, original_root, copied_map, include_raw_media=include_raw_media)
        if rewritten != value:
            changes += 1
        return f"url('{rewritten}')"

    text = CSS_URL_RE.sub(css_replace, text)

    def md_replace(match: re.Match) -> str:
        nonlocal changes, raw_media_replaced
        value = match.group("value")
        replaced_media = is_raw_media_reference(value) and not include_raw_media
        rewritten = rewrite_reference_value(value, source_file, package_root, original_root, copied_map, include_raw_media=include_raw_media)
        if rewritten != value:
            changes += 1
        if replaced_media:
            raw_media_replaced = True
            replacement = match.group(0).replace(value, rewritten)
            return f"{replacement}\n\n> {RAW_MEDIA_PLACEHOLDER_TEXT}\n"
        return match.group(0).replace(value, rewritten)

    text = MD_LINK_RE.sub(md_replace, text)
    if raw_media_replaced and source_file.suffix.lower() in {".html", ".htm"} and RAW_MEDIA_PLACEHOLDER_TEXT not in text:
        text = text.replace("</body>", _raw_media_note() + "</body>") if "</body>" in text else text + _raw_media_note()
        changes += 1
    return text, changes, raw_media_replaced


def _rewrite_json_value(
    value,
    source_file: Path,
    package_root: Path,
    original_root: Path,
    copied_map: dict[str, str],
    key_hint: str = "",
    include_raw_media: bool = False,
):
    if isinstance(value, dict):
        rewritten = {}
        for key, item in value.items():
            rewritten[key] = _rewrite_json_value(item, source_file, package_root, original_root, copied_map, str(key), include_raw_media)
        return rewritten
    if isinstance(value, list):
        return [_rewrite_json_value(item, source_file, package_root, original_root, copied_map, key_hint, include_raw_media) for item in value]
    if isinstance(value, str):
        if _is_provenance_key(key_hint):
            return value
        key_is_live = key_hint.lower() in LIVE_REFERENCE_KEYS
        if not key_is_live and not is_raw_media_reference(value):
            return value
        if not is_raw_media_reference(value) and not is_probably_reference(value):
            return value
        rewritten = rewrite_reference_value(value, source_file, package_root, original_root, copied_map, include_raw_media=include_raw_media)
        if rewritten != value and Path(split_reference(value)[0]).is_absolute():
            return {"package_relative_path": rewritten, "original_source_path": value}
        return rewritten
    return value


def rewrite_package_links(
    package_root: Path,
    original_root: Path,
    copied_map: dict[str, str],
    *,
    include_raw_media: bool = False,
    raw_media_excluded_count: int = 0,
) -> dict:
    write_raw_media_placeholder(package_root, raw_media_excluded_count)
    rewritten_files = []
    raw_media_placeholder_files = []
    total_changes = 0
    for path in sorted(package_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        raw_media_replaced = False
        if path.suffix.lower() == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
            if data is not None:
                rewritten_data = _rewrite_json_value(data, path, package_root, original_root, copied_map, include_raw_media=include_raw_media)
                new_text = json.dumps(rewritten_data, indent=2, ensure_ascii=False)
                changes = 1 if new_text != text else 0
            else:
                new_text, changes, raw_media_replaced = rewrite_text_links(text, path, package_root, original_root, copied_map, include_raw_media=include_raw_media)
        else:
            new_text, changes, raw_media_replaced = rewrite_text_links(text, path, package_root, original_root, copied_map, include_raw_media=include_raw_media)
        if changes:
            path.write_text(new_text, encoding="utf-8")
            total_changes += changes
            rewritten_files.append(package_rel(path, package_root))
        if raw_media_replaced:
            raw_media_placeholder_files.append(package_rel(path, package_root))
    report = {
        "analysis_status": "complete",
        "method": "portable_link_rewrite_v2",
        "generated_at_utc": utc_now_iso(),
        "rewritten_file_count": len(rewritten_files),
        "rewrite_count": total_changes,
        "raw_media_placeholder_inserted": bool(raw_media_placeholder_files),
        "raw_media_placeholder_files": raw_media_placeholder_files,
        "rewritten_files": rewritten_files,
    }
    (package_root / "validation").mkdir(parents=True, exist_ok=True)
    write_json(package_root / "validation" / "portable_link_rewrite_report.json", report)
    return report
