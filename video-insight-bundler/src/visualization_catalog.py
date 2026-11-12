"""Catalog generated visualizations, reports, and evidence artifacts."""

from __future__ import annotations

from pathlib import Path

from intelligence_common import base_artifact
from stability import deterministic_id


def build_visualization_catalog(output_dir: Path, graph_index: dict) -> dict:
    rows = []
    for interp in graph_index.get("graph_interpretations", []):
        rows.append({
            "visualization_id": deterministic_id("VIS", interp.get("graph_id"), interp.get("graph_path")),
            "title": interp.get("graph_title"),
            "path": interp.get("graph_path"),
            "type": "graph",
            "subsystem": interp.get("subsystem"),
            "related_metrics": [interp.get("metric_id")],
            "related_artifacts": interp.get("related_artifact_paths") or [],
            "detail_page": interp.get("detail_page_path"),
            "dashboard_card_enabled": True,
            "review_priority": interp.get("status"),
            "evidence_refs": interp.get("evidence_refs") or [],
        })
    for folder, item_type in [("visualizations", "html"), ("reports", "report"), ("dashboard", "json")]:
        root = output_dir / folder
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".html", ".md", ".json"}:
                rel = path.relative_to(output_dir).as_posix()
                rows.append({
                    "visualization_id": deterministic_id("VIS", rel),
                    "title": path.stem.replace("_", " ").title(),
                    "path": rel,
                    "type": item_type,
                    "subsystem": "dashboard" if folder == "dashboard" else "visualization",
                    "related_metrics": [],
                    "related_artifacts": [],
                    "detail_page": None,
                    "dashboard_card_enabled": path.suffix.lower() == ".html",
                    "review_priority": "review",
                    "evidence_refs": [rel],
                })
    output = base_artifact(method="deterministic_visualization_catalog_v1")
    output.update({
        "visualization_catalog_id": deterministic_id("VCAT", [row["path"] for row in rows]),
        "visualizations": rows,
        "summary": {"visualization_count": len(rows), "dashboard_card_count": sum(1 for row in rows if row.get("dashboard_card_enabled"))},
    })
    return output
