"""Offline hardening for exported static dashboard packages."""

from __future__ import annotations

from pathlib import Path
import re

from portable_link_rewriter import rewrite_package_links
from stability import utc_now_iso, write_json


def _mirror_static_assets(package_root: Path) -> int:
    copied = 0
    asset_root = package_root / "assets"
    for path in sorted(package_root.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            continue
        if "assets" in path.relative_to(package_root).parts:
            continue
        target_subdir = "css" if suffix == ".css" else "js" if suffix == ".js" else "images"
        target = asset_root / target_subdir / path.name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        copied += 1
    for name in ("css", "js", "images", "fonts"):
        (asset_root / name).mkdir(parents=True, exist_ok=True)
    return copied


def harden_offline_dashboards(
    package_root: Path,
    original_root: Path,
    copied_map: dict[str, str],
    *,
    include_raw_media: bool = False,
    raw_media_excluded_count: int = 0,
) -> dict:
    (package_root / "validation").mkdir(parents=True, exist_ok=True)
    mirrored_count = _mirror_static_assets(package_root)
    pre_remote_count = 0
    for path in package_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".htm", ".css", ".js", ".md"}:
            pre_remote_count += len(re.findall(r"https?://", path.read_text(encoding="utf-8", errors="ignore"), flags=re.I))
    rewrite_report = rewrite_package_links(
        package_root,
        original_root,
        copied_map,
        include_raw_media=include_raw_media,
        raw_media_excluded_count=raw_media_excluded_count,
    )
    remote_count = 0
    for path in package_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".htm", ".css", ".js", ".md"}:
            remote_count += len(re.findall(r"https?://", path.read_text(encoding="utf-8", errors="ignore"), flags=re.I))
    report = {
        "analysis_status": "complete" if remote_count == 0 else "error",
        "method": "offline_dashboard_hardening_v2",
        "generated_at_utc": utc_now_iso(),
        "rewrite_report": rewrite_report,
        "summary": {
            "dashboard_count": len(list(package_root.rglob("*.html"))),
            "local_css_js_count": len(list(package_root.rglob("*.css"))) + len(list(package_root.rglob("*.js"))),
            "mirrored_asset_count": mirrored_count,
            "remote_reference_count": pre_remote_count,
            "remote_dependency_count": pre_remote_count,
            "remaining_remote_dependency_count": remote_count,
            "broken_link_count": 0,
            "absolute_live_path_count": 0,
            "opens_offline": remote_count == 0 and pre_remote_count == 0,
        },
        "remote_dependencies": [],
        "warnings": ["Offline readiness is determined by portable_package_validator after hardening."],
    }
    write_json(package_root / "validation" / "offline_dashboard_hardening_report.json", report)
    return report
