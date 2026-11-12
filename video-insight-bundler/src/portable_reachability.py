"""Reachability and audit reports for portable export packages."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from asset_dependency_scanner import classify_file, extract_references, is_text_file, resolve_reference
from stability import utc_now_iso, write_json


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def default_entrypoints(package_root: Path) -> list[str]:
    candidates = [
        "index.html",
        "visualizations/corpus_dashboard.html",
        "visualizations/dashboard.html",
        "dashboard.html",
    ]
    return [item for item in candidates if (package_root / item).exists()]


def _is_intentional_unreachable(rel: str) -> bool:
    lower = rel.lower()
    return any(
        token in lower
        for token in (
            "manifest",
            "validation",
            "exclusion",
            "package_summary",
            "package_size",
            "package_diff",
            "audit",
            "evidence",
            "governance",
            "recommendation",
            "readiness",
        )
    )


def analyze_reachability(package_root: Path, entrypoints: list[str] | None = None) -> dict:
    root = package_root.resolve()
    entries = entrypoints or default_entrypoints(root)
    all_files = {_rel(path, root): path for path in root.rglob("*") if path.is_file()}
    reachable: set[str] = set()
    broken: list[dict] = []
    queue = deque(entries)
    while queue:
        rel = queue.popleft()
        if rel in reachable or rel not in all_files:
            continue
        reachable.add(rel)
        path = all_files[rel]
        if not is_text_file(path):
            continue
        for ref in extract_references(path):
            if ref.get("kind") == "absolute_path":
                continue
            value = str(ref.get("value") or "")
            resolved = resolve_reference(path, root, value)
            if not resolved:
                if value and not value.startswith("#"):
                    broken.append({"source": rel, **ref})
                continue
            try:
                target_rel = _rel(resolved, root)
            except ValueError:
                continue
            if target_rel in all_files and target_rel not in reachable:
                queue.append(target_rel)
    unreachable = sorted(set(all_files) - reachable)
    intentional = [rel for rel in unreachable if _is_intentional_unreachable(rel)]
    suspicious = [rel for rel in unreachable if rel not in intentional]
    reachable_size = sum(all_files[rel].stat().st_size for rel in reachable if rel in all_files)
    total_size = sum(path.stat().st_size for path in all_files.values())
    report = {
        "analysis_status": "complete",
        "method": "portable_reachability_v1",
        "generated_at_utc": utc_now_iso(),
        "entrypoints": entries,
        "reachable_files": sorted(reachable),
        "unreachable_files": unreachable,
        "unreachable_but_intentional": intentional,
        "unreachable_suspicious": suspicious,
        "broken_references": broken,
        "coverage_percent_by_count": round((len(reachable) / max(len(all_files), 1)) * 100, 2),
        "coverage_percent_by_size": round((reachable_size / max(total_size, 1)) * 100, 2),
        "summary": {
            "total_file_count": len(all_files),
            "reachable_file_count": len(reachable),
            "unreachable_file_count": len(unreachable),
            "unreachable_suspicious_count": len(suspicious),
            "broken_reference_count": len(broken),
        },
    }
    write_json(root / "portable_reachability_report.json", report)
    (root / "validation").mkdir(parents=True, exist_ok=True)
    write_json(root / "validation" / "portable_reachability_report.json", report)
    return report


def write_export_audit_report(package_root: Path, reachability: dict, size_report: dict, manifest: dict) -> dict:
    root = package_root.resolve()
    files = manifest.get("files", [])
    by_type: dict[str, list[dict]] = {}
    for row in files:
        by_type.setdefault(str(row.get("artifact_type")), []).append(row)
    linked = set(reachability.get("reachable_files") or [])
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = _rel(path, root)
        kind = classify_file(root, path)
        rows.append(
            {
                "package_path": rel,
                "artifact_type": kind,
                "reachable": rel in linked,
                "human_review_value": "high" if kind in {"dashboard", "html", "graph", "board", "markdown", "recommendation", "evidence", "governance"} else "medium" if kind in {"manifest", "timeline", "interpretation"} else "low",
                "size_bytes": path.stat().st_size,
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "portable_export_audit_v1",
        "generated_at_utc": utc_now_iso(),
        "questions": {
            "actually_linked_or_reachable": sorted(linked),
            "only_indirectly_referenced": reachability.get("reachable_files", []),
            "never_referenced_preserved_for_audit": reachability.get("unreachable_but_intentional", []),
            "human_useful_json": [row.get("package_path") for row in files if row.get("artifact_type") in {"manifest", "interpretation", "recommendation", "evidence", "governance", "timeline"}],
            "low_level_machine_json": [row.get("package_path") for row in files if row.get("artifact_type") in {"json", "schema", "snapshot", "diff", "replay"}],
            "schemas_needed_in_review": [row.get("package_path") for row in files if row.get("artifact_type") == "schema" and row.get("profile_inclusion") in {"audit", "full"}],
            "essential_validation_files": [path for path in reachability.get("unreachable_but_intentional", []) if "validation" in path.lower()],
            "central_markdown_reports": [row.get("package_path") for row in files if str(row.get("package_path", "")).lower().endswith(".md") and any(token in str(row.get("package_path", "")).lower() for token in ("summary", "report", "readme"))],
            "major_dashboard_entrypoints": reachability.get("entrypoints", []),
            "largest_files": size_report.get("largest_files", [])[:25],
            "duplicate_candidates": size_report.get("duplicate_files_by_hash", [])[:25],
            "full_or_audit_only_candidates": reachability.get("unreachable_suspicious", [])[:250],
        },
        "summary": {
            "file_count": len(rows),
            "reachable_count": len(linked),
            "unreachable_suspicious_count": len(reachability.get("unreachable_suspicious", [])),
            "largest_file_count_reported": len(size_report.get("largest_files", [])[:25]),
        },
        "files": rows,
    }
    write_json(root / "portable_export_audit_report.json", report)
    lines = [
        "# Portable Export Audit Report",
        "",
        f"- Files: {report['summary']['file_count']}",
        f"- Reachable files: {report['summary']['reachable_count']}",
        f"- Unreachable suspicious files: {report['summary']['unreachable_suspicious_count']}",
        "",
        "## Largest Files",
    ]
    lines.extend(f"- `{row.get('path')}`: {row.get('size_bytes')} bytes" for row in size_report.get("largest_files", [])[:20])
    lines.extend(["", "## Full/Audit Candidates"])
    lines.extend(f"- `{path}`" for path in reachability.get("unreachable_suspicious", [])[:100])
    (root / "portable_export_audit_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
