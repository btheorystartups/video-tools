"""Machine and human-readable artifact index generation."""

from __future__ import annotations

import json
from pathlib import Path

from stability import TOOL_VERSION


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _existing(root: Path, pattern: str) -> list[str]:
    return sorted(_rel(path, root) for path in root.glob(pattern) if path.is_file())


def build_analysis_index(bundle, manifest: dict, report_data: dict, graph_status: dict, visualization_status: dict) -> dict:
    root = bundle.output_dir
    artifacts = {
        "top_level": _existing(root, "*"),
        "visualizations": _existing(root, "visualizations/*.html"),
        "interactive": _existing(root, "interactive/*.html"),
        "graphs": _existing(root, "graphs/*"),
        "reports": _existing(root, "reports/*"),
        "consensus": _existing(root, "consensus/*"),
        "discourse": _existing(root, "discourse/*"),
        "visual_structure": _existing(root, "visual_structure/*"),
        "revision_graph": _existing(root, "revision_graph/*"),
        "integrity": _existing(root, "integrity/*"),
        "longitudinal": _existing(root, "longitudinal/*"),
        "sequence": _existing(root, "sequence/*"),
        "comparative": _existing(root, "comparative/*"),
        "charts": _existing(root, "charts/*"),
        "frames": _existing(root, "frames/*"),
        "verification_evidence": _existing(root, "verification_evidence/*"),
    }
    recommended = [
        "visualizations/dashboard.html",
        "analysis_index.md",
        "recommendations.json",
        "reports/quality_report.md",
        "reports/revision_graph_summary.md",
        "reports/evidence_consensus_report.md",
        "consensus/evidence_consensus.json",
        "discourse/discourse_summary.json",
        "discourse/argument_graph.json",
        "discourse/editorial_ambiguity.json",
        "visual_structure/visual_structure.json",
        "visual_structure/visual_boundary_alignment.json",
        "visualizations/visual_structure.html",
        "verification_evidence/visual_structure_validation.json",
        "verification_evidence/discourse_schema_validation.json",
        "consensus/transition_confidence.json",
        "verification_evidence/revision_schema_validation.json",
        "revision_graph/revision_graph.json",
        "revision_graph/release_readiness_report.json",
        "integrity/artifact_integrity.json",
        "integrity/graph_consistency.json",
        "integrity/reference_validation.json",
        "integrity/lineage_validation.json",
        "integrity/migration_registry.json",
        "integrity/semantic_readiness.json",
        "visualizations/artifact_integrity.html",
        "visualizations/graph_consistency.html",
        "visualizations/reference_validation.html",
        "visualizations/semantic_readiness.html",
        "longitudinal/longitudinal_summary.json",
        "longitudinal/longitudinal_analysis.json",
        "longitudinal/trend_analysis.json",
        "longitudinal/confidence_volatility.json",
        "longitudinal/persistent_patterns.json",
        "visualizations/longitudinal_analysis.html",
        "verification_evidence/longitudinal_validation.json",
        "sequence/sequence_summary.json",
        "sequence/sequence_structure.json",
        "sequence/temporal_rhythm.json",
        "sequence/editorial_pressure.json",
        "sequence/recommendation_dependencies.json",
        "sequence/revision_propagation.json",
        "sequence/counterfactual_simulation.json",
        "sequence/epistemic_stability.json",
        "comparative/comparative_summary.json",
        "comparative/multi_video_analysis.json",
        "comparative/style_fingerprint.json",
        "comparative/creator_evolution.json",
        "comparative/structural_pattern_mining.json",
        "comparative/semantic_equivalence_scaffolding.json",
        "verification_evidence/temporal_structure_validation.json",
        "verification_evidence/revision_simulation_validation.json",
        "verification_evidence/comparative_validation.json",
        "revision_graph/branch_comparison_report.json",
        "revision_graph/mutation_safety_contract.json",
        "llm_context_bundle.md",
    ]
    return {
        "tool_version": TOOL_VERSION,
        "run_timestamp_utc": manifest.get("generated_at_utc"),
        "source_video": bundle.source_video,
        "source_video_metadata": bundle.media_metadata,
        "subsystem_statuses": manifest.get("subsystem_statuses", {}),
        "warnings": manifest.get("warnings", []),
        "limitations": manifest.get("limitations", []),
        "artifacts": artifacts,
        "recommended_next_review_files": [item for item in recommended if (root / item).exists()],
        "key_metrics": {
            "duration_sec": bundle.media_metadata.get("duration_sec"),
            "word_count": bundle.audio_features.get("word_count"),
            "segment_count": bundle.scene_segments.get("segment_count"),
            "warning_count": len(manifest.get("warnings", [])),
            "quality_scores": report_data.get("quality_scores", {}),
            "topic_drift_score": (getattr(bundle, "topic_analysis", None) or {}).get("topic_drift_score"),
            "silence_ratio": (getattr(bundle, "acoustic_features", None) or {}).get("silence_ratio"),
            "rhetorical_balance_score": (getattr(bundle, "rhetorical_analysis", None) or {}).get("rhetorical_balance_score"),
            "release_readiness_score": _revision_metric(root, "release_readiness_score"),
            "release_readiness_class": _revision_metric(root, "release_readiness_class"),
            "mean_consensus_score": _consensus_metric(root, "mean_consensus_score"),
            "mean_modality_agreement": _consensus_metric(root, "mean_modality_agreement"),
            "false_positive_boundary_ratio": _consensus_metric(root, "false_positive_boundary_ratio"),
            "schema_validation_status": _schema_validation_status(root),
            "argument_completeness_score": _read_json(root / "discourse" / "argument_graph.json").get("argument_completeness_score"),
            "narrative_persistence_score": _read_json(root / "discourse" / "narrative_memory.json").get("thematic_persistence_score"),
            "callback_resolution_quality": _read_json(root / "discourse" / "callback_resolution.json").get("payoff_quality_score"),
            "ambiguity_adjusted_continuity": _read_json(root / "discourse" / "discourse_summary.json").get("ambiguity_adjusted_continuity"),
            "visual_boundary_count": _read_json(root / "visual_structure" / "visual_structure.json").get("shot_boundary_count"),
            "visual_continuity_score": _read_json(root / "visual_structure" / "visual_structure.json").get("visual_continuity_score"),
            "visual_boundary_alignment_quality": _read_json(root / "visual_structure" / "visual_structure.json").get("visual_boundary_alignment_quality"),
            "artifact_integrity_score": _read_json(root / "integrity" / "artifact_integrity.json").get("integrity_score"),
            "graph_consistency_score": _read_json(root / "integrity" / "graph_consistency.json").get("graph_integrity_score"),
            "reference_integrity_score": _read_json(root / "integrity" / "reference_validation.json").get("reference_integrity_score"),
            "lineage_consistency_score": _read_json(root / "integrity" / "lineage_validation.json").get("lineage_consistency_score"),
            "dashboard_coverage_score": _read_json(root / "integrity" / "dashboard_coverage.json").get("dashboard_coverage_score"),
            "longitudinal_confidence": _read_json(root / "longitudinal" / "longitudinal_summary.json").get("longitudinal_confidence"),
            "confidence_volatility_score": _read_json(root / "longitudinal" / "confidence_volatility.json").get("volatility_score"),
            "structural_coherence_score": _read_json(root / "sequence" / "sequence_summary.json").get("structural_coherence_score"),
            "peak_editorial_pressure": _read_json(root / "sequence" / "sequence_summary.json").get("peak_cumulative_pressure_score"),
            "epistemic_stability_score": _read_json(root / "sequence" / "sequence_summary.json").get("epistemic_stability_score"),
            "creator_evolution_classification": _read_json(root / "comparative" / "comparative_summary.json").get("creator_evolution_classification"),
            "comparative_volatility": _read_json(root / "comparative" / "comparative_summary.json").get("comparative_volatility"),
        },
        "consensus_summary": _consensus_summary(root),
        "schema_validation_summary": _schema_validation_summary(root),
        "generation_status": {
            "graphs": graph_status,
            "visualizations": visualization_status,
        },
    }


def write_analysis_index(bundle, manifest: dict, report_data: dict, graph_status: dict, visualization_status: dict) -> dict:
    data = build_analysis_index(bundle, manifest, report_data, graph_status, visualization_status)
    root = bundle.output_dir
    (root / "analysis_index.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Analysis Index",
        "",
        f"- Source: `{bundle.source_video}`",
        f"- Tool version: `{TOOL_VERSION}`",
        f"- Generated: `{data.get('run_timestamp_utc')}`",
        "",
        "## Statuses",
        "",
    ]
    for key, value in data["subsystem_statuses"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Recommended Review Files", ""])
    lines.extend(f"- `{item}`" for item in data["recommended_next_review_files"])
    lines.extend(["", "## Consensus Summary", ""])
    for key, value in data.get("consensus_summary", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Schema Validation", ""])
    schema_summary = data.get("schema_validation_summary", {})
    for key, value in schema_summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Artifact Map", ""])
    for group, paths in data["artifacts"].items():
        lines.append(f"### {group.replace('_', ' ').title()}")
        if paths:
            lines.extend(f"- `{item}`" for item in paths)
        else:
            lines.append("- No files generated.")
        lines.append("")
    lines.extend(["## Warnings", ""])
    if data["warnings"]:
        lines.extend(f"- `{item.get('code')}`: {item.get('message')}" for item in data["warnings"])
    else:
        lines.append("- No structured warnings.")
    (root / "analysis_index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return data


def _revision_metric(root: Path, key: str):
    path = root / "revision_graph" / "release_readiness_report.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(key)
    except Exception:
        return None


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _consensus_summary(root: Path) -> dict:
    consensus = _read_json(root / "consensus" / "evidence_consensus.json")
    transition = _read_json(root / "consensus" / "transition_confidence.json")
    agreement = _read_json(root / "consensus" / "modality_agreement.json")
    scores = _read_json(root / "consensus" / "evidence_score_summary.json")
    false_positive = _read_json(root / "consensus" / "false_positive_boundaries.json")
    return {
        "mean_consensus_score": ((consensus.get("summary", {}) or {}).get("consensus_score_distribution", {}) or {}).get("mean"),
        "modality_agreement_summary": (agreement.get("summary", {}) or {}).get("mean_agreement_score"),
        "weakest_evidence_summary": ", ".join(row.get("modality", "") for row in scores.get("weakest_evidence", [])[:3]),
        "highest_confidence_transitions": ", ".join(row.get("transition_id", "") for row in sorted(transition.get("transitions", []), key=lambda item: (-(item.get("confidence_score") or 0), item.get("transition_id") or ""))[:3]),
        "likely_false_positive_transitions": ", ".join(row.get("transition_id", "") for row in false_positive.get("boundaries", []) if row.get("likely_false_boundary"))[:240],
        "consensus_backed_recommendations": _recommendation_consensus_count(root),
    }


def _consensus_metric(root: Path, key: str):
    summary = _consensus_summary(root)
    if key == "mean_modality_agreement":
        return summary.get("modality_agreement_summary")
    if key == "false_positive_boundary_ratio":
        return _read_json(root / "consensus" / "false_positive_boundaries.json").get("false_positive_boundary_ratio")
    return summary.get(key)


def _recommendation_consensus_count(root: Path) -> int:
    data = _read_json(root / "recommendations.json")
    return sum(1 for row in data.get("recommendations", []) if row.get("consensus_backing"))


def _schema_validation_status(root: Path):
    return _read_json(root / "verification_evidence" / "revision_schema_validation.json").get("validation_status")


def _schema_validation_summary(root: Path) -> dict:
    report = _read_json(root / "verification_evidence" / "revision_schema_validation.json")
    discourse = _read_json(root / "verification_evidence" / "discourse_schema_validation.json")
    visual = _read_json(root / "verification_evidence" / "visual_structure_validation.json")
    return {
        "validation_status": report.get("validation_status"),
        "artifact_count": report.get("artifact_count"),
        "error_count": report.get("error_count"),
        "discourse_validation_status": discourse.get("validation_status"),
        "discourse_error_count": discourse.get("error_count"),
        "visual_structure_validation_status": visual.get("validation_status"),
        "visual_structure_error_count": visual.get("error_count"),
    }
