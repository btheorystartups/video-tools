"""Hierarchical temporal sequence intelligence orchestration."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from counterfactual_simulation import build_counterfactual_simulation
from editorial_pressure import build_editorial_pressure
from epistemic_stability import build_epistemic_stability
from intelligence_common import avg, bar_png, base_artifact, clamp, deterministic_id, line_png, matrix_png, marker_counts, num, placeholder_png, segment_rate, sorted_segments, transition_pairs, write_report, write_simple_html
from narrative_phase_model import build_narrative_phase_model
from recommendation_dependencies import build_recommendation_dependencies
from revision_forecasting import build_revision_forecasting
from revision_propagation import build_revision_propagation
from scene_hierarchy import build_scene_hierarchy
from schema_validation import validate_against_schema
from stability import STATUS_COMPLETE, STATUS_ERROR, write_json
from temporal_rhythm import build_temporal_rhythm


SEQUENCE_ARTIFACTS = {
    "sequence_structure": "sequence_structure.json",
    "scene_hierarchy": "scene_hierarchy.json",
    "temporal_rhythm": "temporal_rhythm.json",
    "narrative_phase_model": "narrative_phase_model.json",
    "editorial_pressure": "editorial_pressure.json",
    "recommendation_dependencies": "recommendation_dependencies.json",
    "revision_propagation": "revision_propagation.json",
    "counterfactual_simulation": "counterfactual_simulation.json",
    "revision_forecasting": "revision_forecasting.json",
    "epistemic_stability": "epistemic_stability.json",
}

SEQUENCE_GRAPHS = {
    "sequence_structure": "sequence_hierarchy_map.png",
    "scene_hierarchy": "sequence_hierarchy_map.png",
    "temporal_rhythm": "pacing_wave_timeline.png",
    "narrative_phase_model": "narrative_phase_map.png",
    "editorial_pressure": "editorial_pressure_curve.png",
    "recommendation_dependencies": "recommendation_dependency_graph.png",
    "revision_propagation": "revision_propagation_graph.png",
    "counterfactual_simulation": "revision_conflict_matrix.png",
    "revision_forecasting": "revision_forecast_heatmap.png",
    "epistemic_stability": "epistemic_stability_curve.png",
}

SEQUENCE_REPORTS = {
    "sequence_structure": "sequence_structure_report.md",
    "temporal_rhythm": "temporal_rhythm_report.md",
    "narrative_phase_model": "narrative_phase_report.md",
    "editorial_pressure": "editorial_pressure_report.md",
    "recommendation_dependencies": "recommendation_dependencies_report.md",
    "revision_propagation": "revision_propagation_report.md",
    "counterfactual_simulation": "counterfactual_simulation_report.md",
    "epistemic_stability": "epistemic_stability_report.md",
}


def _group_class(rate: float, coherence: float, markers: list[str]) -> str:
    if rate >= 175:
        return "escalation_region"
    if rate <= 75:
        return "reset_region"
    if "example" in markers:
        return "release_cycle"
    if coherence >= 0.72:
        return "stability_region"
    return "pacing_region"


def build_sequence_structure(bundle) -> dict:
    segments = sorted_segments(bundle.scene_segments)
    groups = []
    current = []
    last_class = None
    for segment in segments:
        group_class = _group_class(segment_rate(segment), num(segment.get("segment_coherence_score"), 0.35), segment.get("topic_markers") or [])
        if current and group_class != last_class and len(current) >= 2:
            groups.append(_build_group(current, last_class or "sequence_region"))
            current = []
        current.append(segment)
        last_class = group_class
    if current:
        groups.append(_build_group(current, last_class or "sequence_region"))
    pivots = []
    for left, right in transition_pairs(segments):
        rate_shift = clamp(abs(segment_rate(right) - segment_rate(left)) / 140.0)
        marker_shift = 0.24 if set(left.get("topic_markers") or []) != set(right.get("topic_markers") or []) else 0.0
        pivot_score = clamp(rate_shift + marker_shift + abs(num(right.get("segment_coherence_score"), 0.35) - num(left.get("segment_coherence_score"), 0.35)) * 0.36)
        if pivot_score >= 0.32:
            pivots.append(
                {
                    "pivot_id": deterministic_id("PIVOT", left.get("segment_id"), right.get("segment_id"), pivot_score),
                    "from_segment_id": left.get("segment_id"),
                    "to_segment_id": right.get("segment_id"),
                    "pivot_score": pivot_score,
                    "pivot_class": "major" if pivot_score >= 0.58 else "moderate",
                }
            )
    chains = []
    for left, right in transition_pairs(segments):
        shared = sorted(set(left.get("topic_markers") or []) & set(right.get("topic_markers") or []))
        if shared:
            chains.append(
                {
                    "chain_id": deterministic_id("CHAIN", left.get("segment_id"), right.get("segment_id"), shared),
                    "from_segment_id": left.get("segment_id"),
                    "to_segment_id": right.get("segment_id"),
                    "continuity_markers": shared,
                }
            )
    output = base_artifact(method="deterministic_sequence_structure_v1")
    output.update(
        {
            "sequence_id": deterministic_id("SEQ", [row.get("segment_id") for row in segments]),
            "segment_groups": groups,
            "structural_pivots": pivots,
            "continuity_chains": chains,
            "summary": {
                "segment_count": len(segments),
                "group_count": len(groups),
                "structural_pivot_count": len(pivots),
                "continuity_chain_count": len(chains),
                "transition_density": clamp(len(pivots) / max(len(segments) - 1, 1)),
                "structural_coherence_score": clamp(avg([row.get("mean_coherence") for row in groups]) * 0.62 + (1.0 - len(pivots) / max(len(segments), 1)) * 0.38),
                "group_class_counts": dict(sorted(Counter(row.get("group_class") for row in groups).items())),
            },
        }
    )
    return output


def _build_group(rows: list[dict], group_class: str) -> dict:
    markers = marker_counts(rows)
    return {
        "group_id": deterministic_id("SGRP", [row.get("segment_id") for row in rows], group_class),
        "group_class": group_class,
        "segment_ids": [row.get("segment_id") for row in rows],
        "start_sec": rows[0].get("start_sec"),
        "end_sec": rows[-1].get("end_sec"),
        "mean_speech_rate_wpm": avg([segment_rate(row) for row in rows]),
        "mean_coherence": avg([num(row.get("segment_coherence_score"), 0.35) for row in rows]),
        "dominant_markers": [key for key, _ in markers.most_common(4)],
        "buildup_release_role": "buildup" if group_class == "escalation_region" else "release" if group_class in {"reset_region", "release_cycle"} else "stable",
    }


def write_sequence_outputs(bundle) -> dict:
    root = bundle.output_dir
    sequence_dir = root / "sequence"
    reports_dir = root / "reports"
    graphs_dir = root / "graphs"
    vis_dir = root / "visualizations"
    evidence_dir = root / "verification_evidence"
    for directory in (sequence_dir, reports_dir, graphs_dir, vis_dir, evidence_dir):
        directory.mkdir(exist_ok=True)
    sequence = build_sequence_structure(bundle)
    hierarchy = build_scene_hierarchy(bundle, sequence)
    rhythm = build_temporal_rhythm(bundle)
    phases = build_narrative_phase_model(bundle, rhythm)
    pressure = build_editorial_pressure(bundle, rhythm, phases)
    dependencies = build_recommendation_dependencies(bundle, pressure)
    propagation = build_revision_propagation(bundle, dependencies, pressure)
    counterfactual = build_counterfactual_simulation(bundle, propagation, pressure)
    forecasting = build_revision_forecasting(bundle, propagation, counterfactual)
    epistemic = build_epistemic_stability(bundle, dependencies, forecasting, counterfactual)
    summary = {
        "analysis_status": STATUS_COMPLETE,
        "method": "deterministic_sequence_intelligence_summary_v1",
        "sequence_id": sequence.get("sequence_id"),
        "structural_coherence_score": (sequence.get("summary") or {}).get("structural_coherence_score"),
        "mean_intensity_wave_score": (rhythm.get("summary") or {}).get("mean_intensity_wave_score"),
        "peak_cumulative_pressure_score": (pressure.get("summary") or {}).get("peak_cumulative_pressure_score"),
        "recommendation_dependency_pressure": (dependencies.get("summary") or {}).get("recommendation_dependency_pressure"),
        "mean_propagation_uncertainty": (propagation.get("summary") or {}).get("mean_propagation_uncertainty"),
        "mean_counterfactual_uncertainty": (counterfactual.get("summary") or {}).get("mean_counterfactual_uncertainty"),
        "epistemic_stability_score": epistemic.get("stability_score"),
        "classification_guidance": "operational beta+",
        "limitations": sequence.get("limitations", []),
    }
    outputs = {
        "sequence_structure": sequence,
        "scene_hierarchy": hierarchy,
        "temporal_rhythm": rhythm,
        "narrative_phase_model": phases,
        "editorial_pressure": pressure,
        "recommendation_dependencies": dependencies,
        "revision_propagation": propagation,
        "counterfactual_simulation": counterfactual,
        "revision_forecasting": forecasting,
        "epistemic_stability": epistemic,
        "sequence_summary": summary,
    }
    for key, filename in {**SEQUENCE_ARTIFACTS, "sequence_summary": "sequence_summary.json"}.items():
        write_json(sequence_dir / filename, outputs[key])
    _write_sequence_reports(reports_dir, outputs)
    _write_sequence_graphs(graphs_dir, outputs)
    _write_sequence_visualizations(vis_dir, outputs)
    validation = validate_sequence_outputs(root, bundle.schema_path.parent, outputs)
    write_json(evidence_dir / "temporal_structure_validation.json", validation["temporal_structure_validation"])
    write_json(evidence_dir / "revision_simulation_validation.json", validation["revision_simulation_validation"])
    _update_readiness(root, outputs)
    _update_revision_graph(root, outputs)
    return outputs


def _write_sequence_reports(reports_dir: Path, outputs: dict) -> None:
    for key, filename in SEQUENCE_REPORTS.items():
        write_report(reports_dir / filename, key.replace("_", " ").title(), outputs[key])


def _write_sequence_graphs(graphs_dir: Path, outputs: dict) -> None:
    rhythm_rows = outputs["temporal_rhythm"].get("rhythm_segments") or []
    line_png(graphs_dir / "pacing_wave_timeline.png", "Pacing Wave Timeline", [{"label": row.get("segment_id"), "value": row.get("intensity_wave_score")} for row in rhythm_rows])
    line_png(graphs_dir / "temporal_rhythm.png", "Temporal Rhythm", [{"label": row.get("segment_id"), "value": row.get("density_score")} for row in rhythm_rows])
    phase_rows = outputs["narrative_phase_model"].get("phase_segments") or []
    phase_map = {phase: index / 9.0 for index, phase in enumerate(["introduction", "framing", "exploration", "escalation", "expansion", "reflection", "synthesis", "reinforcement", "conclusion", "unresolved_exit"])}
    line_png(graphs_dir / "narrative_phase_map.png", "Narrative Phase Map", [{"label": row.get("segment_id"), "value": phase_map.get(row.get("phase"), 0)} for row in phase_rows])
    pressure_rows = outputs["editorial_pressure"].get("pressure_segments") or []
    line_png(graphs_dir / "editorial_pressure_curve.png", "Editorial Pressure Curve", [{"label": row.get("segment_id"), "value": row.get("cumulative_pressure_score")} for row in pressure_rows])
    line_png(graphs_dir / "contradiction_pressure_curve.png", "Contradiction Pressure Curve", [{"label": row.get("segment_id"), "value": (row.get("components") or {}).get("contradiction_accumulation")} for row in pressure_rows])
    groups = outputs["sequence_structure"].get("segment_groups") or []
    bar_png(graphs_dir / "sequence_hierarchy_map.png", "Sequence Hierarchy Map", [(row.get("group_class"), len(row.get("segment_ids") or [])) for row in groups], "Segments")
    bar_png(graphs_dir / "structural_transition_map.png", "Structural Transition Map", [(row.get("pivot_class"), row.get("pivot_score")) for row in outputs["sequence_structure"].get("structural_pivots", [])])
    bar_png(graphs_dir / "recommendation_dependency_graph.png", "Recommendation Dependency Graph", [(row.get("dependency_type"), row.get("interaction_pressure")) for row in outputs["recommendation_dependencies"].get("dependency_edges", [])])
    bar_png(graphs_dir / "revision_propagation_graph.png", "Revision Propagation Graph", [(row.get("revision_family"), (row.get("estimated_effects") or {}).get("readiness_impact_estimate")) for row in outputs["revision_propagation"].get("propagation_estimates", [])])
    matrix_png(graphs_dir / "revision_conflict_matrix.png", "Revision Conflict Matrix", [[row.get("interaction_pressure") or 0.0] for row in outputs["recommendation_dependencies"].get("dependency_edges", [])], ["pressure"])
    matrix_png(graphs_dir / "revision_forecast_heatmap.png", "Revision Forecast Heatmap", [[row.get("expected_readiness_shift") or 0.0, row.get("forecast_uncertainty") or 0.0] for row in outputs["revision_forecasting"].get("revision_forecasts", [])], ["shift", "uncertainty"])
    line_png(graphs_dir / "epistemic_stability_curve.png", "Epistemic Stability Curve", [{"label": key, "value": value} for key, value in (outputs["epistemic_stability"].get("metric_stability") or {}).items() if value is not None])
    for name in SEQUENCE_GRAPHS.values():
        path = graphs_dir / name
        if not path.exists():
            placeholder_png(path, name, "Graph generated as a graceful placeholder.")


def _write_sequence_visualizations(vis_dir: Path, outputs: dict) -> None:
    links = [(key.replace("_", " ").title(), f"{key}.html") for key in SEQUENCE_ARTIFACTS]
    for key, filename in SEQUENCE_ARTIFACTS.items():
        graph = SEQUENCE_GRAPHS.get(key, "sequence_hierarchy_map.png")
        write_simple_html(vis_dir / f"{key}.html", key.replace("_", " ").title(), "Sequence Intelligence", graph, outputs[key], links)


def validate_sequence_outputs(root: Path, schema_dir: Path, outputs: dict) -> dict:
    temporal_rows = []
    revision_rows = []
    valid_segments = {row.get("segment_id") for row in (outputs["scene_hierarchy"].get("scenes") or []) for row in []}
    scene_segments = {sid for scene in outputs["scene_hierarchy"].get("scenes", []) for sid in scene.get("segment_ids", [])}
    for key, filename in SEQUENCE_ARTIFACTS.items():
        report = validate_against_schema(outputs[key], schema_dir / f"{key}.schema.json")
        row = {"artifact": f"sequence/{filename}", **report}
        if key in {"sequence_structure", "scene_hierarchy", "temporal_rhythm", "narrative_phase_model", "editorial_pressure", "epistemic_stability"}:
            temporal_rows.append(row)
        else:
            revision_rows.append(row)
    reference_errors = []
    for edge in outputs["recommendation_dependencies"].get("dependency_edges", []):
        node_ids = {row.get("recommendation_node_id") for row in outputs["recommendation_dependencies"].get("recommendation_nodes", [])}
        if edge.get("from_recommendation_node_id") not in node_ids or edge.get("to_recommendation_node_id") not in node_ids:
            reference_errors.append({"path": "$.dependency_edges", "message": "Dependency edge references missing recommendation node."})
    for row in outputs["editorial_pressure"].get("pressure_segments", []):
        if scene_segments and row.get("segment_id") not in scene_segments:
            reference_errors.append({"path": "$.pressure_segments", "message": f"Unknown segment reference: {row.get('segment_id')}"})
    reference_row = {"artifact": "sequence_reference_checks", "validation_status": STATUS_COMPLETE if not reference_errors else STATUS_ERROR, "error_count": len(reference_errors), "errors": reference_errors}
    temporal_rows.append(reference_row)
    revision_rows.append(reference_row)
    return {
        "temporal_structure_validation": {
            "validation_status": STATUS_COMPLETE if all(row.get("validation_status") == STATUS_COMPLETE for row in temporal_rows) else STATUS_ERROR,
            "results": temporal_rows,
        },
        "revision_simulation_validation": {
            "validation_status": STATUS_COMPLETE if all(row.get("validation_status") == STATUS_COMPLETE for row in revision_rows) else STATUS_ERROR,
            "results": revision_rows,
        },
    }


def _update_readiness(root: Path, outputs: dict) -> None:
    path = root / "revision_graph" / "release_readiness_report.json"
    data = {}
    if path.exists():
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
    if not data:
        return
    summary = outputs["sequence_summary"]
    components = {
        "structural_coherence": summary.get("structural_coherence_score") or 0.35,
        "temporal_rhythm_stability": clamp(1.0 - (summary.get("mean_intensity_wave_score") or 0.0) * 0.24),
        "editorial_pressure": clamp(1.0 - (summary.get("peak_cumulative_pressure_score") or 0.0)),
        "recommendation_dependency_pressure": clamp(1.0 - (summary.get("recommendation_dependency_pressure") or 0.0)),
        "revision_propagation_risk": clamp(1.0 - (summary.get("mean_propagation_uncertainty") or 0.0)),
        "counterfactual_uncertainty": clamp(1.0 - (summary.get("mean_counterfactual_uncertainty") or 0.0)),
        "epistemic_stability": summary.get("epistemic_stability_score") or 0.35,
        "recurring_structural_debt": clamp(1.0 - (summary.get("peak_cumulative_pressure_score") or 0.0) * 0.5),
    }
    data.setdefault("score_components", {}).update(components)
    data["sequence_intelligence_inputs"] = summary
    base = float(data.get("release_readiness_score") or 0.0)
    sequence_mean = avg(list(components.values()))
    data["release_readiness_score"] = round(min(base, base * 0.88 + sequence_mean * 0.12), 3)
    if summary.get("peak_cumulative_pressure_score", 0) >= 0.72 or summary.get("mean_counterfactual_uncertainty", 0) >= 0.64:
        issue = "Sequence intelligence shows high editorial pressure or counterfactual uncertainty."
        data.setdefault("blocking_issues", [])
        if issue not in data["blocking_issues"]:
            data["blocking_issues"].append(issue)
    write_json(path, data)


def _update_revision_graph(root: Path, outputs: dict) -> None:
    path = root / "revision_graph" / "revision_graph.json"
    if not path.exists():
        return
    import json
    graph = json.loads(path.read_text(encoding="utf-8"))
    graph["sequence_revision_inputs"] = {
        "recommendation_dependencies": outputs["recommendation_dependencies"].get("summary"),
        "revision_propagation": outputs["revision_propagation"].get("summary"),
        "counterfactual_simulation": outputs["counterfactual_simulation"].get("summary"),
        "revision_forecasting": outputs["revision_forecasting"].get("summary"),
        "epistemic_stability": outputs["epistemic_stability"].get("summary"),
        "revision_conflict_awareness": outputs["recommendation_dependencies"].get("dependency_edges", []),
    }
    write_json(path, graph)
