"""Dashboard governance, topology compression, and review navigation reports."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

from asset_dependency_scanner import IMAGE_EXTENSIONS, classify_file, extract_references, is_text_file, resolve_reference
from stability import deterministic_id, utc_now_iso, write_json


DASHBOARD_TAGS = {
    "governance",
    "audit",
    "delta",
    "timeline",
    "recommendation",
    "interpretation",
    "evidence",
    "continuity",
    "benchmark",
    "comparative",
    "review",
    "debug",
    "experimental",
    "internal",
}

REVIEW_PATHWAY_DEFS = {
    "executive_review": ["start", "dashboard", "corpus", "summary", "readiness", "recommendation"],
    "governance_review": ["governance", "conflict", "adjudication", "validation", "integrity"],
    "audit_review": ["audit", "manifest", "validation", "schema", "replay", "snapshot"],
    "recommendation_review": ["recommendation", "optimization", "lineage", "traceability"],
    "continuity_review": ["continuity", "timeline", "longitudinal", "sequence"],
    "evidence_review": ["evidence", "consensus", "reference", "integrity"],
    "delta_review": ["delta", "diff", "regression", "route"],
    "interpretation_review": ["interpretation", "graph", "explanation", "metric"],
}

CORE_ENTRYPOINTS = {
    "index.html",
    "visualizations/corpus_dashboard.html",
    "visualizations/dashboard.html",
    "dashboard.html",
}


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _html_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")[:12000]
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return re.sub(r"<[^>]+>", "", re.sub(r"\s+", " ", match.group(1))).strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def _tokens(rel: str) -> set[str]:
    lower = rel.lower()
    raw = re.split(r"[^a-z0-9]+", lower)
    tokens = {token for token in raw if token}
    if "diff" in tokens:
        tokens.add("delta")
    if "replay" in tokens or "snapshot" in tokens or "schema" in tokens:
        tokens.add("audit")
    if "adjudication" in tokens or "conflict" in tokens:
        tokens.add("governance")
    if "graph" in tokens or "metric" in tokens or "explanation" in tokens:
        tokens.add("interpretation")
    return tokens


def _category(rel: str, artifact_type: str) -> tuple[str, str]:
    tokens = _tokens(rel)
    if "governance" in tokens:
        return "governance", "governance"
    if "recommendation" in tokens or "optimization" in tokens:
        return "recommendation", "lineage" if "lineage" in tokens else "guidance"
    if "evidence" in tokens or "consensus" in tokens:
        return "evidence", "consensus" if "consensus" in tokens else "evidence"
    if "delta" in tokens or "diff" in tokens or "regression" in tokens:
        return "delta", "route" if "route" in tokens else "artifact"
    if "timeline" in tokens or "sequence" in tokens or "continuity" in tokens:
        return "continuity", "timeline" if "timeline" in tokens else "sequence"
    if "interpretation" in tokens or "graph" in tokens or "metric" in tokens:
        return "interpretation", "graph"
    if "benchmark" in tokens or "comparative" in tokens:
        return "comparative", "benchmark" if "benchmark" in tokens else "comparative"
    if "validation" in tokens or "audit" in tokens or "schema" in tokens:
        return "audit", "validation" if "validation" in tokens else "audit"
    if artifact_type == "dashboard":
        return "review", "dashboard"
    return "internal", artifact_type


def _tags(rel: str, category: str, artifact_type: str) -> list[str]:
    tokens = _tokens(rel)
    tags = {category}
    tags.update(token for token in tokens if token in DASHBOARD_TAGS)
    if artifact_type == "dashboard":
        tags.add("review")
    if "debug" in tokens or "trace" in tokens:
        tags.add("debug")
    return sorted(tags & DASHBOARD_TAGS)


def _lifecycle(rel: str, artifact_type: str, reachable: bool, duplicate: bool, drilldown_depth: int) -> tuple[str, str, str]:
    tokens = _tokens(rel)
    if not reachable:
        return "orphaned", "stale_orphan" if any(token in tokens for token in ("old", "stale", "tmp")) else "active", "hidden"
    if "debug" in tokens or "trace" in tokens:
        return "debug", "active", "hidden"
    if "experimental" in tokens or "prototype" in tokens:
        return "experimental", "active", "hidden"
    if "deprecated" in tokens or "superseded" in tokens:
        return "deprecated", "superseded", "hidden"
    if "audit" in tokens or "validation" in tokens or "schema" in tokens or artifact_type in {"schema", "manifest"}:
        return "audit", "active", "advanced"
    if rel in CORE_ENTRYPOINTS or "corpus_dashboard" in rel or rel.endswith("/dashboard.html"):
        return "core", "active", "primary"
    if drilldown_depth >= 3 or "drilldown" in tokens or duplicate:
        return "internal", "active", "hidden" if duplicate else "advanced"
    return "review", "active", "visible"


def _importance(rel: str, artifact_type: str, linked_from: list[str], links_to: list[str], reachable: bool, duplicate: bool, drilldown_depth: int, tags: list[str]) -> dict:
    score = 20
    if rel in CORE_ENTRYPOINTS:
        score += 45
    if reachable:
        score += 15
    if linked_from:
        score += min(20, len(linked_from) * 4)
    if any(source in CORE_ENTRYPOINTS for source in linked_from):
        score += 20
    if artifact_type == "dashboard":
        score += 15
    if any(tag in tags for tag in ("governance", "recommendation", "evidence", "interpretation", "continuity")):
        score += 10
    if "audit" in tags:
        score -= 5
    if duplicate:
        score -= 20
    score -= min(24, drilldown_depth * 6)
    score = max(0, min(100, score))
    review = max(0, min(100, score + (10 if "review" in tags else 0) - (10 if "debug" in tags or "internal" in tags else 0)))
    audit = max(0, min(100, 40 + (25 if "audit" in tags else 0) + (15 if artifact_type in {"manifest", "schema"} else 0) + (10 if reachable else 0)))
    navigation = max(0, min(100, score + min(12, len(links_to) * 2) - (18 if drilldown_depth >= 3 else 0)))
    return {
        "human_importance_score": score,
        "review_importance_score": review,
        "audit_importance_score": audit,
        "navigation_priority_score": navigation,
    }


def _drilldown_depth(rel: str) -> int:
    parts = Path(rel).parts
    depth = max(0, len(parts) - 2)
    lower = rel.lower()
    if "drilldown" in lower:
        depth += 1
    if any(token in lower for token in ("detail/", "/detail_", "lineage", "delta", "diff")):
        depth += 1
    return depth


def _reference_graph(package_root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]], list[dict]]:
    links_to: dict[str, list[str]] = defaultdict(list)
    linked_from: dict[str, list[str]] = defaultdict(list)
    broken: list[dict] = []
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file() or not is_text_file(path):
            continue
        source_rel = _rel(path, package_root)
        for ref in extract_references(path):
            if ref.get("kind") == "absolute_path":
                continue
            value = str(ref.get("value") or "")
            if not value or value.startswith("#"):
                continue
            resolved = resolve_reference(path, package_root, value)
            if not resolved or not resolved.exists() or not resolved.is_file():
                broken.append({"source": source_rel, **ref})
                continue
            try:
                target_rel = _rel(resolved, package_root)
            except ValueError:
                continue
            if target_rel != source_rel:
                links_to[source_rel].append(target_rel)
                linked_from[target_rel].append(source_rel)
    return {key: sorted(set(value)) for key, value in links_to.items()}, {key: sorted(set(value)) for key, value in linked_from.items()}, broken


def _duplicate_lookup(dedupe_report: dict | None) -> dict[str, dict]:
    lookup = {}
    for group in (dedupe_report or {}).get("duplicate_groups") or []:
        files = group.get("files") or []
        canonical = files[0].get("path") if files else None
        for row in files:
            lookup[row.get("path")] = {
                "duplicate_candidate": True,
                "dedupe_group_id": group.get("dedupe_group_id"),
                "canonical_path": canonical,
                "duplicate_bytes": group.get("duplicate_bytes", 0),
            }
    return lookup


def _dashboard_rows(package_root: Path, reachability: dict | None, dedupe_report: dict | None) -> tuple[list[dict], dict[str, list[str]], dict[str, list[str]]]:
    reachable = set((reachability or {}).get("reachable_files") or [])
    links_to, linked_from, _broken = _reference_graph(package_root)
    duplicate_lookup = _duplicate_lookup(dedupe_report)
    rows = []
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file():
            continue
        rel = _rel(path, package_root)
        artifact_type = classify_file(package_root, path)
        if path.suffix.lower() in {".html", ".htm"}:
            artifact_type = "dashboard" if artifact_type == "html" else artifact_type
        category, subcategory = _category(rel, artifact_type)
        tags = _tags(rel, category, artifact_type)
        drilldown_depth = _drilldown_depth(rel)
        duplicate_info = duplicate_lookup.get(rel, {})
        lifecycle_state, lifecycle_status, visibility = _lifecycle(
            rel,
            artifact_type,
            rel in reachable,
            bool(duplicate_info),
            drilldown_depth,
        )
        scores = _importance(
            rel,
            artifact_type,
            linked_from.get(rel, []),
            links_to.get(rel, []),
            rel in reachable,
            bool(duplicate_info),
            drilldown_depth,
            tags,
        )
        row = {
            "dashboard_id": deterministic_id("DASH", rel),
            "title": _html_title(path) if path.suffix.lower() in {".html", ".htm"} else path.name,
            "artifact_type": artifact_type,
            "category": category,
            "subcategory": subcategory,
            "source_generators": ["portable_export_package", "source_analysis_artifact"],
            "generation_reason": "Included in portable analytical review package.",
            "human_review_value": "high" if scores["human_importance_score"] >= 70 else "medium" if scores["human_importance_score"] >= 40 else "low",
            "audit_value": "high" if scores["audit_importance_score"] >= 70 else "medium" if scores["audit_importance_score"] >= 45 else "low",
            "navigation_priority": "start_here" if scores["navigation_priority_score"] >= 80 else "recommended" if scores["navigation_priority_score"] >= 60 else "advanced" if scores["navigation_priority_score"] >= 35 else "hidden",
            "review_priority": "critical" if scores["review_importance_score"] >= 80 else "high" if scores["review_importance_score"] >= 60 else "medium" if scores["review_importance_score"] >= 35 else "low",
            "lifecycle_state": lifecycle_state,
            "lifecycle_status": lifecycle_status,
            "visibility": visibility,
            "entrypoint_status": "entrypoint" if rel in CORE_ENTRYPOINTS else "linked" if linked_from.get(rel) else "not_entrypoint",
            "linked_from": linked_from.get(rel, []),
            "links_to": links_to.get(rel, []),
            "reachable": rel in reachable,
            "orphaned": rel not in reachable,
            "stale": lifecycle_status == "stale" or lifecycle_status == "stale_orphan",
            "superseded_by": duplicate_info.get("canonical_path") if duplicate_info.get("canonical_path") != rel else None,
            "duplicate_candidate": bool(duplicate_info),
            "dedupe_group_id": duplicate_info.get("dedupe_group_id"),
            "drilldown_of": _drilldown_parent(rel, linked_from.get(rel, []), drilldown_depth),
            "child_dashboards": [target for target in links_to.get(rel, []) if Path(target).suffix.lower() in {".html", ".htm"}],
            "estimated_user_value": scores["human_importance_score"],
            "estimated_generation_cost": _cost_score(path),
            "estimated_validation_cost": _validation_cost(path, rel),
            "tags": tags,
            "package_path": rel,
            "drilldown_depth": drilldown_depth,
            **scores,
        }
        rows.append(row)
    return rows, links_to, linked_from


def _drilldown_parent(rel: str, sources: list[str], depth: int) -> str | None:
    if depth <= 0:
        return None
    html_sources = [source for source in sources if Path(source).suffix.lower() in {".html", ".htm"}]
    return html_sources[0] if html_sources else None


def _cost_score(path: Path) -> int:
    size = path.stat().st_size
    return max(1, min(100, int(math.log10(max(size, 1)) * 18)))


def _validation_cost(path: Path, rel: str) -> int:
    base = _cost_score(path)
    if path.suffix.lower() in {".html", ".htm", ".json"}:
        base += 15
    if any(token in rel.lower() for token in ("validation", "schema", "replay", "diff", "delta")):
        base += 15
    return min(100, base)


def _pathway_artifacts(rows: list[dict], tokens: list[str]) -> list[dict]:
    selected = []
    for row in rows:
        haystack = f"{row.get('package_path')} {row.get('title')} {' '.join(row.get('tags') or [])}".lower()
        if any(token in haystack for token in tokens):
            selected.append(row)
    selected.sort(key=lambda row: (row.get("navigation_priority_score", 0), row.get("review_importance_score", 0)), reverse=True)
    return selected[:20]


def _write_review_pathways(package_root: Path, rows: list[dict]) -> dict:
    pathways = []
    for name, tokens in REVIEW_PATHWAY_DEFS.items():
        artifacts = _pathway_artifacts(rows, tokens)
        required = [row["package_path"] for row in artifacts[:5]]
        optional = [row["package_path"] for row in artifacts[5:15]]
        pathways.append(
            {
                "pathway_id": name,
                "recommended_navigation_order": required + optional[:5],
                "critical_dashboards": [path for path in required if path.endswith((".html", ".htm"))],
                "optional_drilldowns": [path for path in optional if "detail" in path.lower() or "drilldown" in path.lower() or "lineage" in path.lower()],
                "estimated_review_time_minutes": max(5, min(90, 4 * len(required) + 2 * len(optional))),
                "required_artifacts": required,
                "pathway_intent": name.replace("_", " "),
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "review_pathways_v57",
        "generated_at_utc": utc_now_iso(),
        "pathways": pathways,
    }
    write_json(package_root / "review_pathways.json", report)
    write_json(package_root / "governance" / "review_pathways.json", report)
    return report


def _write_tag_registry(package_root: Path, rows: list[dict]) -> dict:
    tags = []
    for tag in sorted(DASHBOARD_TAGS):
        tagged = [row for row in rows if tag in (row.get("tags") or [])]
        tags.append(
            {
                "tag": tag,
                "dashboard_count": sum(1 for row in tagged if row.get("artifact_type") == "dashboard"),
                "artifact_count": len(tagged),
                "top_artifacts": [row["package_path"] for row in sorted(tagged, key=lambda item: item.get("navigation_priority_score", 0), reverse=True)[:15]],
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "dashboard_tag_registry_v57",
        "generated_at_utc": utc_now_iso(),
        "tags": tags,
    }
    write_json(package_root / "dashboard_tag_registry.json", report)
    write_json(package_root / "governance" / "dashboard_tag_registry.json", report)
    return report


def _write_importance_registry(package_root: Path, rows: list[dict]) -> dict:
    artifacts = [
        {
            "artifact_path": row["package_path"],
            "artifact_type": row["artifact_type"],
            "category": row["category"],
            "human_importance_score": row["human_importance_score"],
            "review_importance_score": row["review_importance_score"],
            "audit_importance_score": row["audit_importance_score"],
            "navigation_priority_score": row["navigation_priority_score"],
            "scoring_basis": {
                "linked_from_count": len(row.get("linked_from") or []),
                "links_to_count": len(row.get("links_to") or []),
                "reachable": row.get("reachable"),
                "duplicate_candidate": row.get("duplicate_candidate"),
                "drilldown_depth": row.get("drilldown_depth"),
                "tags": row.get("tags") or [],
            },
        }
        for row in sorted(rows, key=lambda item: item.get("human_importance_score", 0), reverse=True)
    ]
    report = {
        "analysis_status": "complete",
        "method": "artifact_importance_scoring_v57",
        "generated_at_utc": utc_now_iso(),
        "artifacts": artifacts,
        "summary": {
            "artifact_count": len(artifacts),
            "critical_review_artifact_count": sum(1 for row in artifacts if row["review_importance_score"] >= 80),
            "high_navigation_artifact_count": sum(1 for row in artifacts if row["navigation_priority_score"] >= 60),
        },
    }
    write_json(package_root / "artifact_importance_registry.json", report)
    write_json(package_root / "governance" / "artifact_importance_registry.json", report)
    return report


def _write_orphan_registry(package_root: Path, rows: list[dict]) -> dict:
    orphans = []
    for row in rows:
        if not row.get("orphaned"):
            continue
        tokens = _tokens(row["package_path"])
        if row.get("lifecycle_state") == "audit" or any(token in tokens for token in ("manifest", "validation", "schema", "audit")):
            status = "intentional_orphan"
        elif row.get("stale"):
            status = "stale_orphan"
        elif row.get("lifecycle_state") in {"debug", "internal"}:
            status = "hidden_internal"
        else:
            status = "orphaned"
        orphans.append(
            {
                "artifact_path": row["package_path"],
                "orphan_status": status,
                "visibility_policy": "hide_from_navigation" if status != "intentional_orphan" else "retain_for_audit",
                "recommended_action": "exclude_if_stale_profile_allows" if status == "stale_orphan" else "review_generation_pattern" if status == "orphaned" else "retain",
                "category": row.get("category"),
                "artifact_type": row.get("artifact_type"),
                "estimated_user_value": row.get("estimated_user_value"),
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "artifact_orphan_governance_v57",
        "generated_at_utc": utc_now_iso(),
        "orphans": orphans,
        "policies": {
            "hide_orphan_pages_from_navigation": True,
            "optionally_exclude_stale_orphans": True,
            "retain_intentional_audit_orphans": True,
            "flag_suspicious_orphan_generation_patterns": True,
        },
        "summary": {
            "orphan_count": len(orphans),
            "suspicious_orphan_count": sum(1 for row in orphans if row["orphan_status"] == "orphaned"),
            "intentional_orphan_count": sum(1 for row in orphans if row["orphan_status"] == "intentional_orphan"),
            "hidden_internal_count": sum(1 for row in orphans if row["orphan_status"] == "hidden_internal"),
        },
    }
    write_json(package_root / "artifact_orphan_registry.json", report)
    write_json(package_root / "governance" / "artifact_orphan_registry.json", report)
    return report


def _write_consolidation_report(package_root: Path, rows: list[dict], consolidation_mode: str) -> dict:
    html_rows = [row for row in rows if row.get("artifact_type") == "dashboard"]
    drilldowns = [row for row in html_rows if row.get("drilldown_depth", 0) >= 2 or "drilldown" in row.get("package_path", "").lower()]
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in drilldowns:
        key = f"{row.get('category')}::{row.get('subcategory')}"
        grouped[key].append(row["package_path"])
    if consolidation_mode == "none":
        pages_after = len(html_rows)
    else:
        kept = [row for row in html_rows if row.get("navigation_priority_score", 0) >= (70 if consolidation_mode == "aggressive" else 55)]
        pages_after = len(kept) + len(grouped)
    report = {
        "analysis_status": "complete",
        "method": "dashboard_consolidation_v57",
        "generated_at_utc": utc_now_iso(),
        "consolidation_mode": consolidation_mode,
        "pages_before": len(html_rows),
        "pages_after": pages_after,
        "grouped_collections": [{"collection_id": key, "page_count": len(paths), "pages": sorted(paths)[:100]} for key, paths in sorted(grouped.items())],
        "eliminated_duplicates": [row["package_path"] for row in html_rows if row.get("duplicate_candidate")],
        "consolidated_drilldowns": [path for paths in grouped.values() for path in sorted(paths)],
        "estimated_navigation_improvement": round((1 - (pages_after / max(len(html_rows), 1))) * 100, 2),
    }
    write_json(package_root / "dashboard_consolidation_report.json", report)
    write_json(package_root / "governance" / "dashboard_consolidation_report.json", report)
    return report


def _write_canonical_asset_registry(package_root: Path) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    display_extensions = IMAGE_EXTENSIONS | {".css", ".js"}
    for path in sorted(package_root.rglob("*"), key=lambda item: item.relative_to(package_root).as_posix().lower()):
        if not path.is_file() or path.suffix.lower() not in display_extensions:
            continue
        rel = _rel(path, package_root)
        if not (
            rel.startswith("graphs/")
            or rel.startswith("assets/")
            or rel.startswith("images/")
            or rel.startswith("visualizations/")
            or rel.startswith("static_assets/")
        ):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups[digest].append({"path": rel, "size_bytes": path.stat().st_size})
    assets = []
    for digest, files in groups.items():
        canonical = sorted(files, key=lambda row: (0 if row["path"].startswith("graphs/") else 1, len(row["path"]), row["path"]))[0]["path"]
        assets.append(
            {
                "asset_hash": digest,
                "canonical_path": canonical,
                "duplicate_paths": [row["path"] for row in files if row["path"] != canonical],
                "ownership_policy": "graphs_preferred_for_graph_assets_else_first_stable_path",
                "display_asset_type": Path(canonical).suffix.lower().lstrip("."),
                "safe_dedupe_candidate": len(files) > 1,
                "files": files,
            }
        )
    report = {
        "analysis_status": "complete",
        "method": "canonical_asset_ownership_v58",
        "generated_at_utc": utc_now_iso(),
        "assets": assets,
        "summary": {
            "asset_group_count": len(assets),
            "duplicate_asset_group_count": sum(1 for row in assets if row["safe_dedupe_candidate"]),
            "duplicate_asset_count": sum(len(row["duplicate_paths"]) for row in assets),
        },
    }
    write_json(package_root / "canonical_asset_registry.json", report)
    write_json(package_root / "governance" / "canonical_asset_registry.json", report)
    return report


def _write_coherence_report(package_root: Path, rows: list[dict], links_to: dict[str, list[str]], consolidation_report: dict) -> dict:
    html_rows = [row for row in rows if row.get("artifact_type") == "dashboard"]
    entrypoints = [row for row in html_rows if row.get("entrypoint_status") == "entrypoint"]
    depths = [row.get("drilldown_depth", 0) for row in html_rows]
    duplicate_clusters = len({row.get("dedupe_group_id") for row in html_rows if row.get("dedupe_group_id")})
    visible = [row for row in html_rows if row.get("visibility") in {"primary", "visible"}]
    category_counts = Counter(row.get("category") for row in visible)
    total_visible = max(len(visible), 1)
    entropy = -sum((count / total_visible) * math.log2(count / total_visible) for count in category_counts.values()) if category_counts else 0
    complexity = len(html_rows) + len([row for row in html_rows if row.get("orphaned")]) * 2 + max(depths or [0]) * 10
    report = {
        "analysis_status": "complete",
        "method": "review_coherence_metrics_v57",
        "generated_at_utc": utc_now_iso(),
        "dashboard_count": len(html_rows),
        "entrypoint_count": len(entrypoints),
        "avg_links_per_dashboard": round(sum(len(links_to.get(row["package_path"], [])) for row in html_rows) / max(len(html_rows), 1), 2),
        "orphan_dashboard_count": sum(1 for row in html_rows if row.get("orphaned")),
        "avg_drilldown_depth": round(sum(depths) / max(len(depths), 1), 2),
        "max_drilldown_depth": max(depths or [0]),
        "duplicate_dashboard_clusters": duplicate_clusters,
        "navigation_entropy_estimate": round(entropy, 3),
        "estimated_review_complexity": complexity,
        "estimated_human_review_hours": round(max(0.25, complexity / 90), 2),
        "topology_compression_ratio": round(consolidation_report.get("pages_after", 0) / max(consolidation_report.get("pages_before", 1), 1), 3),
        "core_dashboard_count": sum(1 for row in html_rows if row.get("lifecycle_state") == "core"),
        "review_dashboard_count": sum(1 for row in html_rows if row.get("lifecycle_state") == "review"),
        "audit_dashboard_count": sum(1 for row in html_rows if row.get("lifecycle_state") == "audit"),
        "debug_dashboard_count": sum(1 for row in html_rows if row.get("lifecycle_state") == "debug"),
    }
    write_json(package_root / "review_coherence_report.json", report)
    write_json(package_root / "governance" / "review_coherence_report.json", report)
    return report


def _write_compressed_review_page(package_root: Path, rows: list[dict], pathways: dict, consolidation: dict, coherence: dict) -> str:
    page_rel = "visualizations/governance/topology_review_system.html"
    page_path = package_root / page_rel
    page_path.parent.mkdir(parents=True, exist_ok=True)
    top = sorted([row for row in rows if row.get("artifact_type") == "dashboard" and not row.get("orphaned")], key=lambda item: item.get("navigation_priority_score", 0), reverse=True)[:24]
    categories: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("artifact_type") == "dashboard" and row.get("visibility") in {"primary", "visible", "advanced"}:
            categories[row.get("category")].append(row)
    category_html = []
    for category, items in sorted(categories.items()):
        items = sorted(items, key=lambda row: row.get("navigation_priority_score", 0), reverse=True)[:40]
        links = "".join(f"<li><a href='../../{row['package_path']}'>{_escape(row['title'])}</a><span>{row['navigation_priority_score']}</span></li>" for row in items)
        category_html.append(f"<details><summary>{_escape(category.title())} ({len(items)})</summary><ul class='ranked'>{links}</ul></details>")
    pathway_html = "".join(
        f"<details><summary>{_escape(pathway['pathway_intent'].title())}</summary><ol>"
        + "".join(f"<li><a href='../../{_escape(path)}'>{_escape(path)}</a></li>" for path in pathway.get("recommended_navigation_order", [])[:12])
        + "</ol></details>"
        for pathway in pathways.get("pathways", [])
    )
    top_html = "".join(f"<a href='../../{row['package_path']}'><strong>{_escape(row['title'])}</strong><span>{_escape(row['category'])} · {row['navigation_priority_score']}</span></a>" for row in top)
    css_link = '<link rel="stylesheet" href="../../static_assets/report.css">' if (package_root / "static_assets" / "report.css").exists() else ""
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review Topology System</title>{css_link}
<style>
.search{{width:100%;max-width:520px;padding:10px;border:1px solid #bbb;border-radius:6px}}.ranked li{{display:flex;justify-content:space-between;gap:12px;margin:6px 0}}
.path-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}}.path-grid a{{display:flex;flex-direction:column;border:1px solid #ddd;background:#fff;padding:10px;border-radius:6px;text-decoration:none}}
details{{border:1px solid #ddd;background:#fff;margin:10px 0;padding:10px;border-radius:6px}}summary{{cursor:pointer;font-weight:700}}
</style></head><body><main class="main expert">
<header class="page-header"><p>Dashboard Governance</p><h1>Review Topology System</h1><p class="muted">Hierarchical navigation over the portable analytical corpus. Audit artifacts remain preserved but are collapsed unless needed.</p></header>
<section class="metrics"><div class="metric"><span>Dashboards</span><strong>{coherence.get('dashboard_count')}</strong></div><div class="metric"><span>Compression</span><strong>{consolidation.get('pages_before')} to {consolidation.get('pages_after')}</strong></div><div class="metric"><span>Orphans</span><strong>{coherence.get('orphan_dashboard_count')}</strong></div><div class="metric"><span>Review hours</span><strong>{coherence.get('estimated_human_review_hours')}</strong></div></section>
<section class="panel"><h2>Search</h2><input class="search" id="filter" placeholder="Filter dashboards, tags, or paths"><script>document.getElementById('filter').addEventListener('input',e=>{{const q=e.target.value.toLowerCase();document.querySelectorAll('li,a').forEach(n=>{{n.style.display=n.textContent.toLowerCase().includes(q)?'':'none'}})}})</script></section>
<section class="panel"><h2>Start Here</h2><div class="path-grid">{top_html}</div></section>
<section class="panel"><h2>Review Pathways</h2>{pathway_html}</section>
<section class="panel"><h2>Categorized Navigation</h2>{''.join(category_html)}</section>
<section class="panel"><h2>Governance Reports</h2><ul><li><a href='../../dashboard_governance_registry.json'>Dashboard governance registry</a></li><li><a href='../../artifact_importance_registry.json'>Artifact importance registry</a></li><li><a href='../../artifact_orphan_registry.json'>Orphan registry</a></li><li><a href='../../dashboard_consolidation_report.json'>Consolidation report</a></li><li><a href='../../review_coherence_report.json'>Review coherence report</a></li></ul></section>
</main></body></html>"""
    page_path.write_text(html, encoding="utf-8")
    return page_rel


def _escape(value: object) -> str:
    return str(value if value is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_dashboard_governance(
    package_root: Path,
    *,
    reachability: dict | None = None,
    dedupe_report: dict | None = None,
    consolidation_mode: str = "grouped",
) -> dict:
    """Generate V57 governance, importance, orphan, topology, and navigation artifacts."""

    if consolidation_mode not in {"none", "grouped", "aggressive"}:
        raise ValueError(f"Unknown consolidation mode: {consolidation_mode}")
    root = package_root.resolve()
    (root / "governance").mkdir(parents=True, exist_ok=True)
    rows, links_to, linked_from = _dashboard_rows(root, reachability, dedupe_report)
    dashboards = [row for row in rows if row.get("artifact_type") == "dashboard"]
    registry = {
        "analysis_status": "complete",
        "method": "dashboard_governance_registry_v57",
        "generated_at_utc": utc_now_iso(),
        "lifecycle_states": ["core", "review", "audit", "debug", "internal", "experimental", "deprecated", "orphaned", "hidden"],
        "lifecycle_statuses": ["active", "stale", "superseded", "generated_once", "transient"],
        "dashboard_count": len(dashboards),
        "artifact_count": len(rows),
        "dashboards": dashboards,
    }
    write_json(root / "dashboard_governance_registry.json", registry)
    write_json(root / "governance" / "dashboard_governance_registry.json", registry)
    importance = _write_importance_registry(root, rows)
    tags = _write_tag_registry(root, rows)
    orphans = _write_orphan_registry(root, rows)
    pathways = _write_review_pathways(root, rows)
    consolidation = _write_consolidation_report(root, rows, consolidation_mode)
    canonical_assets = _write_canonical_asset_registry(root)
    coherence = _write_coherence_report(root, rows, links_to, consolidation)
    topology_page = _write_compressed_review_page(root, rows, pathways, consolidation, coherence)
    summary = {
        "analysis_status": "complete",
        "method": "portable_dashboard_governance_bundle_v57",
        "generated_at_utc": utc_now_iso(),
        "topology_page": topology_page,
        "dashboard_count": len(dashboards),
        "orphan_count": orphans["summary"]["orphan_count"],
        "duplicate_asset_group_count": canonical_assets["summary"]["duplicate_asset_group_count"],
        "topology_compression_ratio": coherence["topology_compression_ratio"],
    }
    write_json(root / "governance" / "dashboard_governance_summary.json", summary)
    return {
        "summary": summary,
        "dashboard_governance_registry": registry,
        "artifact_importance_registry": importance,
        "dashboard_tag_registry": tags,
        "artifact_orphan_registry": orphans,
        "review_pathways": pathways,
        "dashboard_consolidation_report": consolidation,
        "canonical_asset_registry": canonical_assets,
        "review_coherence_report": coherence,
        "topology_page": topology_page,
        "links_to": links_to,
        "linked_from": linked_from,
    }


def validate_dashboard_governance(package_root: Path, governance: dict) -> dict:
    rows = governance.get("dashboard_governance_registry", {}).get("dashboards", [])
    visible = [row for row in rows if row.get("visibility") in {"primary", "visible", "advanced"}]
    top_ranked = sorted(rows, key=lambda row: row.get("navigation_priority_score", 0), reverse=True)[:12]
    missing_metadata = [
        row["package_path"]
        for row in visible
        if not row.get("dashboard_id")
        or not row.get("lifecycle_state")
        or not row.get("category")
        or not row.get("tags")
        or row.get("human_importance_score") is None
    ]
    orphan_rows = governance.get("artifact_orphan_registry", {}).get("orphans", [])
    unclassified_orphans = [row.get("artifact_path") for row in orphan_rows if not row.get("orphan_status")]
    placeholder_pages = {"raw_media_excluded.html", "missing_asset_placeholder.html", "visualizations/governance/topology_review_system.html"}
    exposed_hidden = [
        row["package_path"]
        for row in rows
        if row.get("package_path") not in placeholder_pages
        if row.get("visibility") == "hidden" and any(source in CORE_ENTRYPOINTS for source in row.get("linked_from") or [])
    ]
    graph = {row["package_path"]: [target for target in row.get("links_to", []) if target.endswith((".html", ".htm"))] for row in rows}
    cycles = _cycles(graph)
    duplicate_clusters = len({row.get("dedupe_group_id") for row in rows if row.get("dedupe_group_id")})
    drilldowns = [row for row in rows if row.get("drilldown_depth", 0) >= 2]
    pathways = governance.get("review_pathways", {}).get("pathways", [])
    known_paths = {row["package_path"] for row in rows}
    known_paths.update(path.relative_to(package_root).as_posix() for path in package_root.rglob("*") if path.is_file())
    broken_pathway_links = []
    for pathway in pathways:
        for field in ("recommended_navigation_order", "critical_dashboards", "optional_drilldowns", "required_artifacts"):
            for target in pathway.get(field) or []:
                if target not in known_paths:
                    broken_pathway_links.append({"pathway_id": pathway.get("pathway_id"), "field": field, "target": target})
    category_counts = Counter(row.get("category") for row in visible)
    empty_or_weak_categories = [category for category, count in category_counts.items() if not category or count <= 0]
    search_index = [
        {
            "path": row["package_path"],
            "title": row.get("title"),
            "category": row.get("category"),
            "tags": row.get("tags") or [],
            "visibility": row.get("visibility"),
            "lifecycle_state": row.get("lifecycle_state"),
        }
        for row in visible
    ]
    search_missing = [row["package_path"] for row in visible if row["package_path"] not in {entry["path"] for entry in search_index}]
    top_hidden_or_internal = [
        row["package_path"]
        for row in top_ranked
        if row.get("package_path") not in placeholder_pages
        if row.get("visibility") == "hidden" or row.get("lifecycle_state") in {"debug", "internal"} or "debug" in (row.get("tags") or []) or "internal" in (row.get("tags") or [])
    ]
    top_unreachable = [row["package_path"] for row in top_ranked if not row.get("reachable") and row.get("package_path") not in placeholder_pages]
    superseded_missing_replacement = [row["package_path"] for row in visible if row.get("lifecycle_status") == "superseded" and not row.get("superseded_by")]
    core_missing = not any(row.get("lifecycle_state") == "core" for row in rows)
    flat_index = False
    index_path = package_root / "index.html"
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8", errors="ignore")
        flat_index = text.count("<li><a href=") > 350 and text.count("<details") < 2
    warnings = []
    if len(drilldowns) > max(50, len(rows) * 0.35):
        warnings.append("excessive_drilldown_explosion_detected")
    suspicious_orphans = governance.get("artifact_orphan_registry", {}).get("summary", {}).get("suspicious_orphan_count", 0)
    orphan_threshold = max(100, int(max(len(rows), 1) * 2.0), 500 if len(rows) > 500 else 100)
    if suspicious_orphans > orphan_threshold:
        warnings.append("orphan_overload_detected")
    if cycles:
        warnings.append("dashboard_cycles_detected")
    failures = []
    if core_missing:
        failures.append("core_dashboard_missing")
    if flat_index:
        failures.append("flat_unstructured_index_detected")
    if broken_pathway_links:
        failures.append("broken_review_pathway_links")
    if suspicious_orphans > orphan_threshold:
        failures.append("orphan_overload_exceeds_threshold")
    if top_hidden_or_internal:
        failures.append("hidden_or_internal_pages_top_ranked")
    if top_unreachable:
        failures.append("top_ranked_dashboard_unreachable")
    if missing_metadata:
        failures.append("visible_dashboard_metadata_incomplete")
    if unclassified_orphans:
        failures.append("orphan_classification_missing")
    report = {
        "analysis_status": "complete",
        "method": "dashboard_governance_validation_v58",
        "generated_at_utc": utc_now_iso(),
        "core_dashboard_missing": core_missing,
        "flat_unstructured_index": flat_index,
        "excessive_drilldown_explosion": "excessive_drilldown_explosion_detected" in warnings,
        "duplicate_navigation_loops": bool(cycles),
        "orphan_overload": "orphan_overload_detected" in warnings,
        "orphan_overload_threshold": orphan_threshold,
        "broken_hierarchy_chains": [row["package_path"] for row in rows if row.get("drilldown_of") and row.get("drilldown_of") not in graph],
        "dashboard_cycles": cycles[:25],
        "visible_dashboard_metadata_missing": missing_metadata,
        "unclassified_orphans": unclassified_orphans,
        "broken_pathway_links": broken_pathway_links,
        "category_groups": dict(sorted(category_counts.items())),
        "empty_or_weak_categories": empty_or_weak_categories,
        "search_index_missing_visible_pages": search_missing,
        "top_hidden_or_internal_pages": top_hidden_or_internal,
        "top_unreachable_dashboards": top_unreachable,
        "superseded_missing_replacement": superseded_missing_replacement,
        "duplicate_dashboard_clusters": duplicate_clusters,
        "hidden_dashboards_exposed_accidentally": exposed_hidden,
        "validation_passed": not failures and not exposed_hidden,
        "failures": failures,
        "warnings": warnings,
        "summary": {
            "dashboard_count": len(rows),
            "visible_dashboard_count": len(visible),
            "drilldown_dashboard_count": len(drilldowns),
            "hidden_exposed_count": len(exposed_hidden),
            "cycle_count": len(cycles),
            "broken_pathway_link_count": len(broken_pathway_links),
            "search_index_entry_count": len(search_index),
            "top_unreachable_count": len(top_unreachable),
            "duplicate_dashboard_clusters": duplicate_clusters,
        },
    }
    write_json(package_root / "validation" / "dashboard_governance_validation.json", report)
    write_json(package_root / "dashboard_governance_validation.json", report)
    topology = {
        "analysis_status": "complete" if report["validation_passed"] else "error",
        "method": "topology_hardening_v58",
        "generated_at_utc": utc_now_iso(),
        "index_is_flat": flat_index,
        "audit_only_collapsed_by_default": index_path.exists()
        and (
            "Advanced / Audit-Only Dashboards" in index_path.read_text(encoding="utf-8", errors="ignore")
            or "Advanced Audit Material" in index_path.read_text(encoding="utf-8", errors="ignore")
        ),
        "hidden_internal_in_main_navigation": exposed_hidden,
        "category_groups": dict(sorted(category_counts.items())),
        "dashboard_cycles": cycles[:25],
        "stale_prioritized": [row["package_path"] for row in top_ranked if row.get("stale")],
        "superseded_missing_replacement": superseded_missing_replacement,
        "summary": report["summary"],
    }
    pathway_report = {
        "analysis_status": "complete" if not broken_pathway_links else "error",
        "method": "review_pathway_validation_v58",
        "generated_at_utc": utc_now_iso(),
        "pathway_count": len(pathways),
        "broken_pathway_links": broken_pathway_links,
        "validation_passed": not broken_pathway_links,
        "summary": {"pathway_count": len(pathways), "broken_pathway_link_count": len(broken_pathway_links)},
    }
    search_report = {
        "analysis_status": "complete" if not search_missing else "error",
        "method": "dashboard_search_filter_index_v58",
        "generated_at_utc": utc_now_iso(),
        "entries": search_index,
        "missing_visible_pages": search_missing,
        "summary": {"entry_count": len(search_index), "missing_visible_page_count": len(search_missing)},
    }
    write_json(package_root / "topology_hardening_report.json", topology)
    write_json(package_root / "validation" / "topology_hardening_report.json", topology)
    write_json(package_root / "review_pathway_validation.json", pathway_report)
    write_json(package_root / "validation" / "review_pathway_validation.json", pathway_report)
    write_json(package_root / "dashboard_search_filter_index.json", search_report)
    write_json(package_root / "governance" / "dashboard_search_filter_index.json", search_report)
    return report


def _cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles = []
    visited = set()
    stack = []
    in_stack = set()

    def visit(node: str) -> None:
        if node in in_stack:
            idx = stack.index(node)
            cycles.append(stack[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        stack.append(node)
        for target in graph.get(node, []):
            if target in graph:
                visit(target)
        stack.pop()
        in_stack.remove(node)

    for node in graph:
        visit(node)
    return cycles
