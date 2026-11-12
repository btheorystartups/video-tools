"""Editorial workbench index and static HTML writers."""

from __future__ import annotations

import json
from pathlib import Path

from intelligence_common import base_artifact, deterministic_id, write_simple_html
from stability import write_json


def build_workbench_index(corpus_output_dir: Path, analyses: list[dict], review_queue: dict, corpus_outputs: dict) -> dict:
    video_links = []
    for analysis in analyses:
        analysis_dir = Path(analysis.get("analysis_dir"))
        dashboard = analysis_dir / "visualizations" / "dashboard.html"
        try:
            href = dashboard.resolve().relative_to((corpus_output_dir / "visualizations").resolve())
        except Exception:
            href = dashboard
        video_links.append(
            {
                "source_video": (analysis.get("manifest") or {}).get("source_video"),
                "analysis_dir": str(analysis_dir),
                "dashboard_path": str(dashboard),
            }
        )
    output = base_artifact(method="deterministic_editorial_workbench_index_v1")
    output.update(
        {
            "editorial_workbench_id": deterministic_id("WORK", [row.get("dashboard_path") for row in video_links], review_queue.get("review_queue_id")),
            "video_dashboards": video_links,
            "review_queue_ref": "workbench/review_queue.json",
            "governance_ref": "governance/governance_summary.json",
            "corpus_summary_ref": "corpus/corpus_summary.json",
            "summary": {
                "video_dashboard_count": len(video_links),
                "review_item_count": (review_queue.get("summary") or {}).get("review_item_count"),
                "high_priority_count": (review_queue.get("summary") or {}).get("high_priority_count"),
            },
        }
    )
    return output


def write_workbench_outputs(corpus_output_dir: Path, analyses: list[dict], review_queue: dict, corpus_outputs: dict) -> dict:
    workbench_dir = corpus_output_dir / "workbench"
    vis_dir = corpus_output_dir / "visualizations"
    workbench_dir.mkdir(exist_ok=True)
    vis_dir.mkdir(exist_ok=True)
    workbench = build_workbench_index(corpus_output_dir, analyses, review_queue, corpus_outputs)
    write_json(workbench_dir / "editorial_workbench.json", workbench)
    write_json(workbench_dir / "review_queue.json", review_queue)
    write_json(workbench_dir / "priority_review_items.json", {"analysis_status": review_queue["analysis_status"], "method": "deterministic_priority_review_items_v1", "review_items": review_queue.get("review_items", [])[:50], "limitations": review_queue.get("limitations", [])})
    for key, filename in [
        ("segment_review_index", "segment_review_index.json"),
        ("recommendation_review_index", "recommendation_review_index.json"),
        ("pressure_review_index", "pressure_review_index.json"),
    ]:
        write_json(workbench_dir / filename, {"analysis_status": review_queue["analysis_status"], "method": f"deterministic_{key}_v1", key: (review_queue.get("indexes") or {}).get(key, []), "limitations": review_queue.get("limitations", [])})
    _write_html(corpus_output_dir, workbench, review_queue, corpus_outputs)
    return workbench


def _write_html(corpus_output_dir: Path, workbench: dict, review_queue: dict, corpus_outputs: dict) -> None:
    vis = corpus_output_dir / "visualizations"
    links = [
        ("Corpus Dashboard", "corpus_dashboard.html"),
        ("Corpus Intelligence", "corpus_intelligence.html"),
        ("Corpus Fingerprint", "corpus_fingerprint.html"),
        ("Archetypes", "editorial_archetypes.html"),
        ("Comparative Stabilization", "comparative_stabilization.html"),
        ("Audit Trail", "audit_trail.html"),
        ("Validation Replay", "validation_replay.html"),
        ("Provenance", "provenance_reconstruction.html"),
        ("Workbench", "editorial_workbench.html"),
        ("Review Queue", "review_queue.html"),
        ("Readiness Arbitration", "readiness_arbitration.html"),
        ("RC Assessment", "rc_assessment.html"),
    ]
    pages = {
        "corpus_dashboard.html": ("Corpus Dashboard", "corpus_readiness_matrix.png", corpus_outputs.get("corpus_summary") or {}),
        "corpus_intelligence.html": ("Corpus Intelligence", "corpus_pressure_heatmap.png", corpus_outputs.get("corpus_intelligence") or {}),
        "corpus_fingerprint.html": ("Corpus Fingerprint", "corpus_style_fingerprint_map.png", corpus_outputs.get("corpus_fingerprint") or {}),
        "editorial_archetypes.html": ("Editorial Archetypes", "recurring_archetypes_map.png", corpus_outputs.get("editorial_archetypes") or {}),
        "comparative_stabilization.html": ("Comparative Stabilization", "comparative_stability_curve.png", corpus_outputs.get("comparative_stabilization") or {}),
        "audit_trail.html": ("Audit Trail", "validation_replay_status.png", corpus_outputs.get("audit_trail") or {}),
        "validation_replay.html": ("Validation Replay", "validation_replay_status.png", corpus_outputs.get("validation_replay") or {}),
        "provenance_reconstruction.html": ("Provenance Reconstruction", "validation_replay_status.png", corpus_outputs.get("provenance_reconstruction") or {}),
        "editorial_workbench.html": ("Editorial Workbench", "review_priority_matrix.png", workbench),
        "review_queue.html": ("Review Queue", "review_priority_matrix.png", review_queue),
        "readiness_arbitration.html": ("Readiness Arbitration", "governance_readiness_radar.png", corpus_outputs.get("readiness_arbitration") or {}),
        "rc_assessment.html": ("RC Assessment", "governance_readiness_radar.png", corpus_outputs.get("rc_assessment") or {}),
    }
    for filename, (title, graph, data) in pages.items():
        write_simple_html(vis / filename, title, "Corpus Workbench", graph, data, links)
