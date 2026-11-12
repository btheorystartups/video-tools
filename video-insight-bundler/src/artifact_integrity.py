"""Global artifact integrity orchestration and reporting."""

from __future__ import annotations

import json
import re
from pathlib import Path

from graph_consistency import validate_graph_consistency, write_graph_consistency_report
from lineage_validation import validate_lineage, write_lineage_report
from migration_registry import build_migration_registry, write_migration_report
from reference_validation import EXPECTED_CORE_ARTIFACTS, existing_relative_paths, read_json, validate_references, write_reference_report
from semantic_readiness import build_semantic_readiness, write_semantic_readiness_report
from stability import STATUS_COMPLETE, STATUS_ERROR, STATUS_LIMITED, utc_now_iso, write_json

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


INTEGRITY_GRAPHS = [
    "artifact_dependency_graph.png",
    "graph_consistency_matrix.png",
    "orphan_reference_map.png",
    "lineage_flow_graph.png",
    "dashboard_coverage_heatmap.png",
    "schema_dependency_graph.png",
    "semantic_readiness_map.png",
]

INTEGRITY_PAGES = [
    "artifact_integrity.html",
    "graph_consistency.html",
    "reference_validation.html",
    "lineage_validation.html",
    "migration_registry.html",
    "semantic_readiness.html",
]


def _score_from_issues(issue_count: int, total: int) -> float:
    return round(max(0.0, 1.0 - issue_count / max(total, 1)), 3)


def _html_links(path: Path) -> list[str]:
    if not path.exists() or path.suffix.lower() != ".html":
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    refs = re.findall(r"""(?:href|src)=["']([^"']+)["']""", text)
    return [ref for ref in refs if not ref.startswith(("http://", "https://", "mailto:", "#"))]


def validate_dashboard_coverage(output_dir: Path) -> dict:
    root = Path(output_dir)
    existing = existing_relative_paths(root)
    html_files = sorted((root / "visualizations").glob("*.html")) if (root / "visualizations").exists() else []
    linked = set()
    dead = []
    for html in html_files:
        source_rel = html.relative_to(root).as_posix()
        for link in _html_links(html):
            candidate = (html.parent / link).resolve()
            try:
                rel = candidate.relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
            linked.add(rel)
            if rel not in existing:
                dead.append({"source": source_rel, "target": link, "resolved": rel})
    graphs = {item for item in existing if item.startswith("graphs/")}
    visualizations = {item for item in existing if item.startswith("visualizations/") and item.endswith(".html")}
    reports = {item for item in existing if item.startswith("reports/")}
    dashboard = root / "visualizations" / "dashboard.html"
    dashboard_links = set()
    if dashboard.exists():
        for link in _html_links(dashboard):
            try:
                dashboard_links.add((dashboard.parent / link).resolve().relative_to(root.resolve()).as_posix())
            except ValueError:
                pass
    orphan_visualizations = sorted(visualizations - dashboard_links - {"visualizations/dashboard.html"})
    orphan_graphs = sorted(graphs - linked)
    orphan_reports = sorted(reports - linked)
    issue_count = len(dead) + len(orphan_visualizations) + len(orphan_graphs)
    score = _score_from_issues(issue_count, len(graphs) + len(visualizations) + len(reports))
    report = {
        "validation_status": STATUS_COMPLETE if not dead else STATUS_ERROR,
        "generated_at_utc": utc_now_iso(),
        "dashboard_coverage_score": score,
        "html_page_count": len(visualizations),
        "graph_count": len(graphs),
        "report_count": len(reports),
        "dead_dashboard_entries": dead,
        "orphan_visualizations": orphan_visualizations[:200],
        "orphan_graphs": orphan_graphs[:200],
        "orphan_reports": orphan_reports[:200],
        "coverage_summary": {
            "linked_asset_count": len(linked),
            "dashboard_link_count": len(dashboard_links),
            "all_generated_graphs_reachable": len(orphan_graphs) == 0,
            "all_html_pages_linked_from_dashboard": len(orphan_visualizations) == 0,
        },
        "limitations": ["Coverage checks relative links and generated files only."],
    }
    integrity = root / "integrity"
    integrity.mkdir(exist_ok=True)
    write_json(integrity / "dashboard_coverage.json", report)
    return report


def validate_artifact_integrity(output_dir: Path, schema_dir: Path) -> dict:
    root = Path(output_dir)
    integrity_dir = root / "integrity"
    integrity_dir.mkdir(exist_ok=True)
    existing = existing_relative_paths(root)
    missing = [item for item in EXPECTED_CORE_ARTIFACTS if item not in existing]
    manifest = read_json(root / "manifest.json")
    manifest_artifacts = set()
    for value in (manifest.get("artifacts") or {}).values():
        if isinstance(value, str) and not value.endswith("/"):
            manifest_artifacts.add(value)
    manifest_missing = sorted(item for item in manifest_artifacts if item not in existing)
    schema_summary = {
        "bundle": read_json(root / "verification_evidence" / "schema_validation_results.json").get("validation_status"),
        "revision": read_json(root / "verification_evidence" / "revision_schema_validation.json").get("validation_status"),
        "discourse": read_json(root / "verification_evidence" / "discourse_schema_validation.json").get("validation_status"),
        "continuity": read_json(root / "verification_evidence" / "continuity_schema_validation.json").get("validation_status"),
        "visual_structure": read_json(root / "verification_evidence" / "visual_structure_validation.json").get("validation_status"),
    }
    dashboard = read_json(integrity_dir / "dashboard_coverage.json")
    references = read_json(integrity_dir / "reference_validation.json")
    graphs = read_json(integrity_dir / "graph_consistency.json")
    lineage = read_json(integrity_dir / "lineage_validation.json")
    issue_count = len(missing) + len(manifest_missing)
    issue_count += int(references.get("invalid_reference_count") or 0)
    issue_count += len(graphs.get("invalid_edges") or [])
    issue_count += len(lineage.get("lineage_issues") or [])
    issue_count += len(dashboard.get("dead_dashboard_entries") or [])
    score = _score_from_issues(issue_count, max(len(EXPECTED_CORE_ARTIFACTS) + len(existing), 1))
    report = {
        "validation_status": STATUS_COMPLETE if issue_count == 0 else STATUS_LIMITED,
        "generated_at_utc": utc_now_iso(),
        "integrity_score": score,
        "missing_artifacts": missing + [f"manifest:{item}" for item in manifest_missing],
        "orphan_artifacts": {
            "visualizations": dashboard.get("orphan_visualizations", []),
            "graphs": dashboard.get("orphan_graphs", []),
            "reports": dashboard.get("orphan_reports", []),
        },
        "stale_artifacts": [],
        "unresolved_references": references.get("unresolved_reference_paths", []),
        "dashboard_gaps": dashboard,
        "schema_validation_summary": schema_summary,
        "validation_summary": {
            "reference_integrity_score": references.get("reference_integrity_score"),
            "graph_integrity_score": graphs.get("graph_integrity_score"),
            "lineage_consistency_score": lineage.get("lineage_consistency_score"),
            "dashboard_coverage_score": dashboard.get("dashboard_coverage_score"),
            "artifact_count": len(existing),
        },
        "limitations": [
            "Integrity validation is local and deterministic; it does not infer semantic truth.",
            "Staleness is limited to manifest/reference consistency unless prior-run history is retained.",
        ],
    }
    write_json(integrity_dir / "artifact_integrity.json", report)
    return report


def write_dashboard_coverage_report(output_dir: Path, report: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Dashboard Coverage Report",
        "",
        f"- Score: `{report.get('dashboard_coverage_score')}`",
        f"- HTML pages: `{report.get('html_page_count')}`",
        f"- Graphs: `{report.get('graph_count')}`",
        f"- Reports: `{report.get('report_count')}`",
        "",
        "## Dead Entries",
        "",
    ]
    if report.get("dead_dashboard_entries"):
        for item in report["dead_dashboard_entries"][:50]:
            lines.append(f"- `{item.get('source')}` -> `{item.get('resolved')}`")
    else:
        lines.append("- No dead dashboard links detected.")
    (reports / "dashboard_coverage_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_artifact_integrity_report(output_dir: Path, report: dict) -> None:
    reports = Path(output_dir) / "reports"
    reports.mkdir(exist_ok=True)
    lines = [
        "# Artifact Integrity Report",
        "",
        f"- Integrity score: `{report.get('integrity_score')}`",
        f"- Missing artifacts: `{len(report.get('missing_artifacts') or [])}`",
        f"- Unresolved references: `{len(report.get('unresolved_references') or [])}`",
        "",
        "## Validation Summary",
        "",
    ]
    for key, value in (report.get("validation_summary") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Missing Artifacts", ""])
    if report.get("missing_artifacts"):
        lines.extend(f"- `{item}`" for item in report["missing_artifacts"])
    else:
        lines.append("- No required artifacts missing.")
    (reports / "artifact_integrity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _placeholder_png(path: Path, title: str, rows: list[tuple[str, float]]) -> None:
    if plt:
        fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
        fig.patch.set_facecolor("#f7f7f4")
        ax.set_facecolor("#f7f7f4")
        labels = [row[0] for row in rows] or ["no data"]
        values = [row[1] for row in rows] or [0]
        ax.bar(labels, values, color=["#386b8f", "#5d7f62", "#a7783a", "#9c4f45", "#6d668c"][: len(labels)])
        ax.set_ylim(0, 1)
        ax.set_title(title, loc="left")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
    else:
        try:
            from PIL import Image, ImageDraw

            image = Image.new("RGB", (1200, 640), "#f7f7f4")
            draw = ImageDraw.Draw(image)
            draw.text((40, 40), title, fill="#242424")
            for index, (label, value) in enumerate(rows):
                draw.text((40, 90 + index * 28), f"{label}: {value}", fill="#242424")
            image.save(path)
        except Exception:
            path.write_text(title + "\n", encoding="utf-8")


def write_integrity_graphs(output_dir: Path, outputs: dict) -> None:
    graphs = Path(output_dir) / "graphs"
    graphs.mkdir(exist_ok=True)
    integrity = outputs.get("artifact_integrity", {})
    graph = outputs.get("graph_consistency", {})
    ref = outputs.get("reference_validation", {})
    lineage = outputs.get("lineage_validation", {})
    dashboard = outputs.get("dashboard_coverage", {})
    migration = outputs.get("migration_registry", {})
    semantic = outputs.get("semantic_readiness", {})
    score_rows = [
        ("artifact", integrity.get("integrity_score") or 0),
        ("graph", graph.get("graph_integrity_score") or 0),
        ("reference", ref.get("reference_integrity_score") or 0),
        ("lineage", lineage.get("lineage_consistency_score") or 0),
        ("dashboard", dashboard.get("dashboard_coverage_score") or 0),
    ]
    _placeholder_png(graphs / "artifact_dependency_graph.png", "Artifact Dependency Graph", score_rows)
    _placeholder_png(graphs / "graph_consistency_matrix.png", "Graph Consistency Matrix", [("valid", graph.get("graph_integrity_score") or 0), ("invalid", min(len(graph.get("invalid_edges") or []) / 10, 1))])
    _placeholder_png(graphs / "orphan_reference_map.png", "Orphan Reference Map", [("valid", ref.get("reference_integrity_score") or 0), ("orphan", min((ref.get("orphan_reference_count") or 0) / 10, 1))])
    _placeholder_png(graphs / "lineage_flow_graph.png", "Lineage Flow Graph", [("lineage", lineage.get("lineage_consistency_score") or 0), ("issues", min(len(lineage.get("lineage_issues") or []) / 10, 1))])
    _placeholder_png(graphs / "dashboard_coverage_heatmap.png", "Dashboard Coverage Heatmap", [("coverage", dashboard.get("dashboard_coverage_score") or 0), ("dead", min(len(dashboard.get("dead_dashboard_entries") or []) / 10, 1))])
    _placeholder_png(graphs / "schema_dependency_graph.png", "Schema Dependency Graph", [("schemas", min(len(migration.get("schema_versions") or {}) / 40, 1)), ("hooks", min(len(migration.get("future_migration_hooks") or []) / 10, 1))])
    _placeholder_png(graphs / "semantic_readiness_map.png", "Semantic Readiness Map", [("ready", min(len(semantic.get("semantic_ready_components") or []) / 8, 1)), ("hooks", min(len(semantic.get("future_embedding_hook_points") or []) / 8, 1))])


def _page(title: str, body: str) -> str:
    nav = "".join(f"<a href='{name}'>{name.replace('.html', '').replace('_', ' ').title()}</a>" for name in INTEGRITY_PAGES)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="../static_assets/report.css"></head>
<body><aside class="sidebar"><div class="brand">Integrity</div><nav><a href="dashboard.html">Dashboard</a>{nav}</nav></aside>
<main class="main">{body}</main></body></html>
"""


def _json_block(data: dict) -> str:
    return "<section class='panel'><pre>" + json.dumps(data, indent=2, ensure_ascii=False).replace("&", "&amp;").replace("<", "&lt;") + "</pre></section>"


def write_integrity_visualizations(output_dir: Path, outputs: dict) -> None:
    vis = Path(output_dir) / "visualizations"
    vis.mkdir(exist_ok=True)
    pages = {
        "artifact_integrity.html": ("Artifact Integrity", "artifact_dependency_graph.png", outputs.get("artifact_integrity", {})),
        "graph_consistency.html": ("Graph Consistency", "graph_consistency_matrix.png", outputs.get("graph_consistency", {})),
        "reference_validation.html": ("Reference Validation", "orphan_reference_map.png", outputs.get("reference_validation", {})),
        "lineage_validation.html": ("Lineage Validation", "lineage_flow_graph.png", outputs.get("lineage_validation", {})),
        "migration_registry.html": ("Migration Registry", "schema_dependency_graph.png", outputs.get("migration_registry", {})),
        "semantic_readiness.html": ("Semantic Readiness", "semantic_readiness_map.png", outputs.get("semantic_readiness", {})),
    }
    for filename, (title, graph, data) in pages.items():
        body = f"<header class='page-header'><p>Integrity System</p><h1>{title}</h1></header><section class='grid two'><figure class='graph'><img src='../graphs/{graph}' alt='{title}'></figure></section>{_json_block(data)}"
        (vis / filename).write_text(_page(title, body), encoding="utf-8")


def write_integrity_validation_evidence(output_dir: Path, outputs: dict) -> None:
    evidence = Path(output_dir) / "verification_evidence"
    evidence.mkdir(exist_ok=True)
    write_json(evidence / "integrity_validation.json", {
        "validation_status": outputs.get("artifact_integrity", {}).get("validation_status"),
        "integrity_score": outputs.get("artifact_integrity", {}).get("integrity_score"),
        "reference_integrity_score": outputs.get("reference_validation", {}).get("reference_integrity_score"),
        "dashboard_coverage_score": outputs.get("dashboard_coverage", {}).get("dashboard_coverage_score"),
    })
    write_json(evidence / "graph_validation.json", {
        "validation_status": outputs.get("graph_consistency", {}).get("validation_status"),
        "graph_integrity_score": outputs.get("graph_consistency", {}).get("graph_integrity_score"),
        "lineage_consistency_score": outputs.get("lineage_validation", {}).get("lineage_consistency_score"),
    })
    write_json(evidence / "migration_validation.json", {
        "validation_status": outputs.get("migration_registry", {}).get("validation_status"),
        "migration_registry_version": outputs.get("migration_registry", {}).get("migration_registry_version"),
        "semantic_readiness_version": outputs.get("semantic_readiness", {}).get("semantic_readiness_version"),
    })


def update_release_readiness_with_integrity(output_dir: Path, outputs: dict) -> dict:
    path = Path(output_dir) / "revision_graph" / "release_readiness_report.json"
    readiness = read_json(path)
    if not readiness:
        return {}
    scores = {
        "artifact_integrity_score": outputs.get("artifact_integrity", {}).get("integrity_score", 0.0),
        "graph_consistency_score": outputs.get("graph_consistency", {}).get("graph_integrity_score", 0.0),
        "reference_integrity_score": outputs.get("reference_validation", {}).get("reference_integrity_score", 0.0),
        "lineage_consistency_score": outputs.get("lineage_validation", {}).get("lineage_consistency_score", 0.0),
        "dashboard_coverage_score": outputs.get("dashboard_coverage", {}).get("dashboard_coverage_score", 0.0),
    }
    readiness.setdefault("score_components", {}).update(scores)
    readiness.setdefault("integrity_inputs", {}).update(scores)
    blocking = readiness.setdefault("blocking_issues", [])
    managed_blocking = {
        "Artifact integrity subsystem reported low structural consistency.",
        "Unresolved artifact or graph references were detected.",
        "Revision lineage inconsistencies were detected.",
    }
    blocking[:] = [item for item in blocking if item not in managed_blocking]
    if any(value < 0.75 for value in scores.values()):
        message = "Artifact integrity subsystem reported low structural consistency."
        if message not in blocking:
            blocking.append(message)
    if outputs.get("reference_validation", {}).get("invalid_reference_count", 0):
        message = "Unresolved artifact or graph references were detected."
        if message not in blocking:
            blocking.append(message)
    if outputs.get("lineage_validation", {}).get("lineage_issues"):
        message = "Revision lineage inconsistencies were detected."
        if message not in blocking:
            blocking.append(message)
    base_score = float(readiness.get("release_readiness_score") or 0.0)
    integrity_mean = sum(float(value or 0.0) for value in scores.values()) / max(len(scores), 1)
    readiness["release_readiness_score"] = round(min(base_score, (base_score * 0.82) + (integrity_mean * 0.18)), 3)
    if blocking or readiness["release_readiness_score"] < 0.5:
        readiness["release_readiness_class"] = "not_ready"
    elif readiness["release_readiness_score"] < 0.68:
        readiness["release_readiness_class"] = "review_ready"
    elif readiness["release_readiness_score"] < 0.82:
        readiness["release_readiness_class"] = "dry_run_ready"
    else:
        readiness["release_readiness_class"] = "release_candidate"
    write_json(path, readiness)
    graph_path = Path(output_dir) / "revision_graph" / "revision_graph.json"
    graph = read_json(graph_path)
    if graph:
        graph["release_readiness"] = readiness
        write_json(graph_path, graph)
    return readiness


def run_integrity_suite(output_dir: Path, schema_dir: Path) -> dict:
    reference = validate_references(output_dir)
    graph = validate_graph_consistency(output_dir)
    lineage = validate_lineage(output_dir)
    migration = build_migration_registry(output_dir, schema_dir)
    semantic = build_semantic_readiness(output_dir)
    outputs = {
        "artifact_integrity": {},
        "graph_consistency": graph,
        "reference_validation": reference,
        "lineage_validation": lineage,
        "dashboard_coverage": {},
        "migration_registry": migration,
        "semantic_readiness": semantic,
    }
    write_integrity_graphs(output_dir, outputs)
    write_integrity_visualizations(output_dir, outputs)
    dashboard = validate_dashboard_coverage(output_dir)
    outputs["dashboard_coverage"] = dashboard
    artifact = validate_artifact_integrity(output_dir, schema_dir)
    outputs["artifact_integrity"] = artifact
    write_artifact_integrity_report(output_dir, artifact)
    write_graph_consistency_report(output_dir, graph)
    write_reference_report(output_dir, reference)
    write_lineage_report(output_dir, lineage)
    write_dashboard_coverage_report(output_dir, dashboard)
    write_migration_report(output_dir, migration)
    write_semantic_readiness_report(output_dir, semantic)
    write_integrity_graphs(output_dir, outputs)
    write_integrity_visualizations(output_dir, outputs)
    dashboard = validate_dashboard_coverage(output_dir)
    outputs["dashboard_coverage"] = dashboard
    artifact = validate_artifact_integrity(output_dir, schema_dir)
    outputs["artifact_integrity"] = artifact
    write_artifact_integrity_report(output_dir, artifact)
    write_dashboard_coverage_report(output_dir, dashboard)
    write_integrity_graphs(output_dir, outputs)
    write_integrity_visualizations(output_dir, outputs)
    write_integrity_validation_evidence(output_dir, outputs)
    outputs["release_readiness"] = update_release_readiness_with_integrity(output_dir, outputs)
    return outputs
