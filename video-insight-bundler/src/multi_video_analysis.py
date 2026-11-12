"""Multi-video comparative intelligence orchestration."""

from __future__ import annotations

from pathlib import Path

from comparative_recommendations import build_comparative_recommendations
from creator_evolution import build_creator_evolution
from discourse_fingerprint import build_discourse_fingerprint
from intelligence_common import avg, bar_png, base_artifact, clamp, deterministic_id, line_png, load_analysis_folder, matrix_png, placeholder_png, read_json, write_report, write_simple_html
from pacing_fingerprint import build_pacing_fingerprint
from rhetorical_fingerprint import build_rhetorical_fingerprint
from schema_validation import validate_against_schema
from semantic_equivalence_scaffolding import build_semantic_equivalence_scaffolding
from stability import STATUS_COMPLETE, STATUS_ERROR, write_json
from structural_pattern_mining import build_structural_pattern_mining
from style_fingerprint import build_style_fingerprint


COMPARATIVE_ARTIFACTS = {
    "multi_video_analysis": "multi_video_analysis.json",
    "style_fingerprint": "style_fingerprint.json",
    "rhetorical_fingerprint": "rhetorical_fingerprint.json",
    "pacing_fingerprint": "pacing_fingerprint.json",
    "discourse_fingerprint": "discourse_fingerprint.json",
    "creator_evolution": "creator_evolution.json",
    "structural_pattern_mining": "structural_pattern_mining.json",
    "comparative_recommendations": "comparative_recommendations.json",
    "semantic_equivalence_scaffolding": "semantic_equivalence_scaffolding.json",
}

COMPARATIVE_GRAPHS = {
    "multi_video_analysis": "comparative_continuity_matrix.png",
    "style_fingerprint": "stylistic_similarity_map.png",
    "rhetorical_fingerprint": "rhetorical_signature_map.png",
    "pacing_fingerprint": "pacing_fingerprint_map.png",
    "discourse_fingerprint": "discourse_signature_map.png",
    "creator_evolution": "creator_evolution_timeline.png",
    "structural_pattern_mining": "recurring_pattern_heatmap.png",
    "comparative_recommendations": "recommendation_convergence_graph.png",
    "semantic_equivalence_scaffolding": "semantic_equivalence_readiness_map.png",
}


def build_multi_video_analysis(analyses: list[dict], structural_patterns: dict | None = None) -> dict:
    rows = []
    for index, analysis in enumerate(analyses):
        sequence = analysis.get("sequence_structure") or {}
        pressure = analysis.get("editorial_pressure") or {}
        readiness = analysis.get("release_readiness") or {}
        rows.append(
            {
                "video_analysis_id": deterministic_id("MVID", analysis.get("analysis_dir"), index),
                "analysis_dir": analysis.get("analysis_dir"),
                "source_video": (analysis.get("manifest") or {}).get("source_video"),
                "structural_coherence_score": (sequence.get("summary") or {}).get("structural_coherence_score"),
                "peak_pressure_score": (pressure.get("summary") or {}).get("peak_cumulative_pressure_score"),
                "release_readiness_score": readiness.get("release_readiness_score"),
                "recommendation_count": len((analysis.get("recommendations") or {}).get("recommendations") or []),
            }
        )
    output = base_artifact(method="deterministic_multi_video_comparative_intelligence_v1")
    output.update(
        {
            "multi_video_analysis_id": deterministic_id("MULTI", [row.get("video_analysis_id") for row in rows]),
            "analysis_items": rows,
            "recurring_structures": (structural_patterns or {}).get("recurring_patterns", []),
            "summary": {
                "analysis_count": len(rows),
                "mean_structural_coherence": avg([row.get("structural_coherence_score") for row in rows]),
                "mean_peak_pressure": avg([row.get("peak_pressure_score") for row in rows]),
                "comparative_volatility": clamp(max([row.get("release_readiness_score") or 0 for row in rows], default=0) - min([row.get("release_readiness_score") or 0 for row in rows], default=0)),
            },
        }
    )
    return output


def write_comparative_outputs(output_dir: Path, schema_dir: Path, analysis_dirs: list[Path] | None = None) -> dict:
    comparative_dir = output_dir / "comparative"
    reports_dir = output_dir / "reports"
    graphs_dir = output_dir / "graphs"
    vis_dir = output_dir / "visualizations"
    evidence_dir = output_dir / "verification_evidence"
    for directory in (comparative_dir, reports_dir, graphs_dir, vis_dir, evidence_dir):
        directory.mkdir(exist_ok=True)
    dirs = analysis_dirs or [output_dir]
    analyses = [load_analysis_folder(Path(path)) for path in dirs if Path(path).exists()]
    if not analyses:
        analyses = [load_analysis_folder(output_dir)]
    style = build_style_fingerprint(analyses)
    rhetorical = build_rhetorical_fingerprint(analyses)
    pacing = build_pacing_fingerprint(analyses)
    discourse = build_discourse_fingerprint(analyses)
    creator = build_creator_evolution(analyses, style, rhetorical, pacing, discourse)
    patterns = build_structural_pattern_mining(analyses)
    multi = build_multi_video_analysis(analyses, patterns)
    recommendations = build_comparative_recommendations(analyses, patterns, creator)
    semantic = build_semantic_equivalence_scaffolding()
    summary = {
        "analysis_status": STATUS_COMPLETE,
        "method": "deterministic_comparative_intelligence_summary_v1",
        "analysis_count": len(analyses),
        "creator_evolution_classification": creator.get("classification"),
        "style_fingerprint_id": style.get("style_fingerprint_id"),
        "recurring_pattern_count": (patterns.get("summary") or {}).get("recurring_pattern_count"),
        "comparative_volatility": (multi.get("summary") or {}).get("comparative_volatility"),
        "semantic_scaffold_status": (semantic.get("summary") or {}).get("semantic_readiness_status"),
        "classification_guidance": "operational beta+",
        "limitations": semantic.get("limitations", []),
    }
    outputs = {
        "multi_video_analysis": multi,
        "style_fingerprint": style,
        "rhetorical_fingerprint": rhetorical,
        "pacing_fingerprint": pacing,
        "discourse_fingerprint": discourse,
        "creator_evolution": creator,
        "structural_pattern_mining": patterns,
        "comparative_recommendations": recommendations,
        "semantic_equivalence_scaffolding": semantic,
        "comparative_summary": summary,
    }
    for key, filename in {**COMPARATIVE_ARTIFACTS, "comparative_summary": "comparative_summary.json"}.items():
        write_json(comparative_dir / filename, outputs[key])
    _write_reports(reports_dir, outputs)
    _write_graphs(graphs_dir, outputs)
    _write_visualizations(vis_dir, outputs)
    validation = validate_comparative_outputs(schema_dir, outputs)
    write_json(evidence_dir / "comparative_validation.json", validation)
    _update_readiness(output_dir, outputs)
    _update_consensus(output_dir, outputs)
    return outputs


def _write_reports(reports_dir: Path, outputs: dict) -> None:
    names = {
        "multi_video_analysis": "multi_video_analysis_report.md",
        "style_fingerprint": "style_fingerprint_report.md",
        "rhetorical_fingerprint": "rhetorical_fingerprint_report.md",
        "pacing_fingerprint": "pacing_fingerprint_report.md",
        "discourse_fingerprint": "discourse_fingerprint_report.md",
        "creator_evolution": "creator_evolution_report.md",
        "structural_pattern_mining": "structural_pattern_report.md",
        "comparative_recommendations": "comparative_recommendations_report.md",
        "semantic_equivalence_scaffolding": "semantic_equivalence_scaffolding_report.md",
    }
    for key, filename in names.items():
        write_report(reports_dir / filename, key.replace("_", " ").title(), outputs[key])


def _write_graphs(graphs_dir: Path, outputs: dict) -> None:
    multi_rows = outputs["multi_video_analysis"].get("analysis_items") or []
    matrix_png(graphs_dir / "comparative_continuity_matrix.png", "Comparative Continuity Matrix", [[row.get("structural_coherence_score") or 0.0, row.get("peak_pressure_score") or 0.0] for row in multi_rows], ["coherence", "pressure"])
    bar_png(graphs_dir / "stylistic_similarity_map.png", "Stylistic Similarity Map", [(row.get("analysis_dir"), row.get("structural_rhythm_signature") or 0.0) for row in outputs["style_fingerprint"].get("style_fingerprints", [])])
    bar_png(graphs_dir / "rhetorical_signature_map.png", "Rhetorical Signature Map", [(row.get("dominant_rhetorical_signature"), row.get("rhetorical_density") or 0.0) for row in outputs["rhetorical_fingerprint"].get("rhetorical_fingerprints", [])])
    bar_png(graphs_dir / "pacing_fingerprint_map.png", "Pacing Fingerprint Map", [(row.get("analysis_dir"), row.get("pacing_wave_profile") or 0.0) for row in outputs["pacing_fingerprint"].get("pacing_fingerprints", [])])
    bar_png(graphs_dir / "discourse_signature_map.png", "Discourse Signature Map", [(row.get("analysis_dir"), row.get("discourse_pressure_signature") or 0.0) for row in outputs["discourse_fingerprint"].get("discourse_fingerprints", [])])
    line_png(graphs_dir / "creator_evolution_timeline.png", "Creator Evolution Timeline", [{"label": row.get("sequence_index"), "value": row.get("readiness_score")} for row in outputs["creator_evolution"].get("evolution_points", [])])
    bar_png(graphs_dir / "recurring_pattern_heatmap.png", "Recurring Pattern Heatmap", [(row.get("pattern_type"), row.get("pattern_pressure") or 0.0) for row in outputs["structural_pattern_mining"].get("recurring_patterns", [])])
    bar_png(graphs_dir / "creator_stability_curve.png", "Creator Stability Curve", [("stability", (outputs["creator_evolution"].get("summary") or {}).get("creator_stability_score") or 0.0)])
    bar_png(graphs_dir / "recommendation_convergence_graph.png", "Recommendation Convergence Graph", [(row.get("issue_type"), row.get("convergence_score") or 0.0) for row in outputs["comparative_recommendations"].get("comparative_recommendations", [])])
    bar_png(graphs_dir / "semantic_equivalence_readiness_map.png", "Semantic Equivalence Readiness Map", [("hooks", len(outputs["semantic_equivalence_scaffolding"].get("future_hook_points") or [])), ("runtime", 0.0)], "Count")
    for name in COMPARATIVE_GRAPHS.values():
        if not (graphs_dir / name).exists():
            placeholder_png(graphs_dir / name, name, "Graph generated as a graceful placeholder.")


def _write_visualizations(vis_dir: Path, outputs: dict) -> None:
    links = [(key.replace("_", " ").title(), f"{key}.html") for key in COMPARATIVE_ARTIFACTS]
    for key in COMPARATIVE_ARTIFACTS:
        write_simple_html(vis_dir / f"{key}.html", key.replace("_", " ").title(), "Comparative Intelligence", COMPARATIVE_GRAPHS.get(key, "comparative_continuity_matrix.png"), outputs[key], links)


def validate_comparative_outputs(schema_dir: Path, outputs: dict) -> dict:
    rows = []
    for key, filename in COMPARATIVE_ARTIFACTS.items():
        rows.append({"artifact": f"comparative/{filename}", **validate_against_schema(outputs[key], schema_dir / f"{key}.schema.json")})
    ids = {row.get("video_analysis_id") for row in outputs["multi_video_analysis"].get("analysis_items", [])}
    reference_errors = []
    if not ids:
        reference_errors.append({"path": "$.analysis_items", "message": "No comparative analysis items were loaded."})
    rows.append({"artifact": "comparative_reference_checks", "validation_status": STATUS_COMPLETE if not reference_errors else STATUS_ERROR, "error_count": len(reference_errors), "errors": reference_errors})
    return {
        "validation_status": STATUS_COMPLETE if all(row.get("validation_status") == STATUS_COMPLETE for row in rows) else STATUS_ERROR,
        "results": rows,
        "comparative_reference_count": len(ids),
        "limitations": ["Comparative validation checks local schemas and deterministic analysis-folder references."],
    }


def _update_readiness(output_dir: Path, outputs: dict) -> None:
    path = output_dir / "revision_graph" / "release_readiness_report.json"
    readiness = read_json(path)
    if not readiness:
        return
    summary = outputs["comparative_summary"]
    components = {
        "creator_stability": (outputs["creator_evolution"].get("summary") or {}).get("creator_stability_score") or 0.35,
        "comparative_volatility": clamp(1.0 - (summary.get("comparative_volatility") or 0.0)),
        "recurring_structural_debt": clamp(1.0 - ((outputs["structural_pattern_mining"].get("summary") or {}).get("chronic_pressure_region_count") or 0) / 6.0),
    }
    readiness.setdefault("score_components", {}).update(components)
    readiness["comparative_intelligence_inputs"] = summary
    base = float(readiness.get("release_readiness_score") or 0.0)
    readiness["release_readiness_score"] = round(min(base, base * 0.93 + avg(list(components.values())) * 0.07), 3)
    write_json(path, readiness)


def _update_consensus(output_dir: Path, outputs: dict) -> None:
    path = output_dir / "consensus" / "evidence_consensus.json"
    consensus = read_json(path)
    if not consensus:
        return
    consensus["comparative_consensus_inputs"] = {
        "creator_level_stability": (outputs["creator_evolution"].get("summary") or {}).get("creator_stability_score"),
        "comparative_continuity_stability": (outputs["multi_video_analysis"].get("summary") or {}).get("mean_structural_coherence"),
        "recurring_contradiction_regions": outputs["structural_pattern_mining"].get("recurring_contradiction_regions", []),
        "recurring_discourse_pressure": (outputs["discourse_fingerprint"].get("summary") or {}).get("mean_discourse_pressure"),
    }
    write_json(path, consensus)
