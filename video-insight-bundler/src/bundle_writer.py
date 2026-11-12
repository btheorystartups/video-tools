"""Writers for manifest, LLM markdown, JSON bundles, and simple chart data."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from analysis_index import write_analysis_index
from artifact_integrity import run_integrity_suite
from argument_graph import build_argument_graph
from boundary_diagnostics import analyze_boundary_diagnostics, attach_boundary_diagnostics
from callback_resolution import analyze_callback_resolution
from dependency_diagnostics import dependency_versions
from discourse_state import analyze_discourse_state
from editorial_ambiguity import analyze_editorial_ambiguity, build_discourse_summary
from evidence_consensus import build_evidence_consensus, write_consensus_outputs
from evidence_scoring import build_evidence_score_summary
from graph_builder import build_graphs
from longitudinal_analysis import write_longitudinal_outputs
from multi_video_analysis import write_comparative_outputs
from narrative_memory import analyze_narrative_memory
from recommendation_engine import enrich_recommendations_with_consensus, enrich_recommendations_with_discourse, enrich_recommendations_with_visual
from report_generator import write_reports
from run_comparison import compare_runs
from run_history import build_run_snapshot, load_snapshots, write_run_history
from revision_graph import build_revision_graph, write_disabled_revision_status
from revision_schema_validation import validate_revision_artifacts
from schema_validation import validate_against_schema, write_validation_report
from rhetorical_coherence import analyze_rhetorical_coherence
from topic_continuity import analyze_topic_continuity
from stability import (
    STATUS_COMPLETE,
    STATUS_ERROR,
    STATUS_LIMITED,
    STATUS_SKIPPED,
    STATUS_UNAVAILABLE,
    TOOL_VERSION,
    normalize_status,
    utc_now_iso,
    warning,
)
from visualization_writer import write_visualizations
from visual_structure import build_visual_structure_outputs
from sequence_structure import write_sequence_outputs


@dataclass
class AnalysisBundle:
    source_video: str
    output_dir: Path
    media_metadata: dict
    audio_result: dict
    transcript: dict
    audio_features: dict
    visual_index: dict
    scene_segments: dict
    emotional_arc: dict
    persona_profile: dict
    teaching_profile: dict
    recommendations_md: str
    profile: dict
    profile_path: str
    profile_hash: str
    dependency_report: dict
    warnings: list[dict]
    start_timestamp_utc: str
    execution_duration_sec: float
    schema_path: Path
    evidence_dir: Path
    acoustic_features: dict | None = None
    topic_analysis: dict | None = None
    rhetorical_analysis: dict | None = None
    topic_continuity: dict | None = None
    rhetorical_coherence: dict | None = None
    boundary_diagnostics: dict | None = None
    recommendations_json: dict | None = None
    enable_revision_graph: bool = True
    revision_profile: dict | None = None
    revision_profile_path: str | None = None
    consensus_outputs: dict | None = None
    discourse_state: dict | None = None
    argument_graph: dict | None = None
    narrative_memory: dict | None = None
    callback_resolution: dict | None = None
    editorial_ambiguity: dict | None = None
    discourse_summary: dict | None = None
    visual_structure: dict | None = None
    shot_boundaries: dict | None = None
    visual_continuity: dict | None = None
    composition_features: dict | None = None
    visual_boundary_alignment: dict | None = None
    sequence_outputs: dict | None = None
    comparative_outputs: dict | None = None


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _ensure_history_placeholders(output_dir: Path) -> None:
    for directory in ("history", "longitudinal", "reports", "graphs", "visualizations"):
        (output_dir / directory).mkdir(exist_ok=True)
    for name in ("run_history.html", "artifact_drift.html", "metric_drift.html", "readiness_drift.html"):
        path = output_dir / "visualizations" / name
        if not path.exists():
            path.write_text("<!doctype html><meta charset='utf-8'><title>Run History</title><main>Pending history comparison.</main>", encoding="utf-8")
    for name in ("longitudinal_analysis.html", "trend_analysis.html", "confidence_volatility.html", "recommendation_evolution.html", "anomaly_clusters.html", "persistent_patterns.html", "semantic_evolution.html"):
        path = output_dir / "visualizations" / name
        if not path.exists():
            path.write_text("<!doctype html><meta charset='utf-8'><title>Longitudinal</title><main>Pending longitudinal analysis.</main>", encoding="utf-8")
    for name in ("readiness_drift_timeline.png", "metric_drift_heatmap.png", "artifact_drift_matrix.png", "dependency_drift_timeline.png"):
        path = output_dir / "graphs" / name
        if not path.exists():
            path.write_bytes(b"")
    for name in ("readiness_trend.png", "continuity_trend.png", "contradiction_trend.png", "confidence_volatility_curve.png", "recommendation_evolution_map.png", "persistent_weakness_heatmap.png", "anomaly_cluster_graph.png", "discourse_evolution_timeline.png", "semantic_readiness_timeline.png"):
        path = output_dir / "graphs" / name
        if not path.exists():
            path.write_bytes(b"")
    for name in ("run_comparison.json", "artifact_drift_report.json", "metric_drift_report.json", "readiness_drift_report.json"):
        path = output_dir / "history" / name
        if not path.exists():
            _write_json(path, {"analysis_status": "pending", "generated_at_utc": utc_now_iso()})
    for name in ("longitudinal_analysis.json", "trend_analysis.json", "confidence_volatility.json", "recommendation_evolution.json", "anomaly_clusters.json", "persistent_patterns.json", "semantic_evolution.json", "longitudinal_summary.json"):
        path = output_dir / "longitudinal" / name
        if not path.exists():
            _write_json(path, {"analysis_status": "pending", "generated_at_utc": utc_now_iso()})
    validation_path = output_dir / "verification_evidence" / "longitudinal_validation.json"
    if not validation_path.exists():
        _write_json(validation_path, {"validation_status": "pending", "generated_at_utc": utc_now_iso(), "results": []})


def _clear_regenerated_history_reports(output_dir: Path) -> None:
    for relative in (
        "history/run_comparison.json",
        "history/artifact_drift_report.json",
        "history/metric_drift_report.json",
        "history/schema_version_diff.json",
        "history/dependency_drift_report.json",
        "history/readiness_drift_report.json",
        "reports/run_history_report.md",
        "reports/artifact_drift_report.md",
        "reports/metric_drift_report.md",
        "reports/readiness_drift_report.md",
    ):
        path = output_dir / relative
        if path.exists() and path.is_file():
            path.unlink()


def _segment_table(segments: list[dict]) -> str:
    lines = ["| Segment | Time | Words | Rate | Summary |", "| --- | ---: | ---: | ---: | --- |"]
    for segment in segments:
        lines.append(
            f"| {segment.get('segment_id')} | {segment.get('start_sec')}-{segment.get('end_sec')}s | "
            f"{segment.get('word_count')} | {segment.get('speech_rate_wpm')} | {segment.get('summary') or '[no transcript]'} |"
        )
    return "\n".join(lines)


def _profile_lines(profile: dict) -> list[str]:
    lines = []
    for category in profile.get("top_categories", [])[:5]:
        evidence = ", ".join(category.get("evidence", [])[:5]) or "limited evidence"
        lines.append(f"- {category.get('label')}: {category.get('weight')} evidence: {evidence}")
    return lines or ["- No strong classification available."]


def _write_markdown_bundle(bundle: AnalysisBundle) -> None:
    transcript_text = bundle.transcript.get("text", "")
    excerpt = transcript_text[:3000] + ("..." if len(transcript_text) > 3000 else "")
    lines = [
        "# LLM Context Bundle",
        "",
        "Use this bundle as context for a future GPT/Codex review. It is generated locally and includes measured metadata plus transparent heuristics.",
        "",
        "## Source Video Metadata",
        "",
        f"- Source: `{bundle.source_video}`",
        f"- Duration: `{bundle.media_metadata.get('duration_sec')}` seconds",
        f"- Resolution: `{bundle.media_metadata.get('width')}x{bundle.media_metadata.get('height')}`",
        f"- FPS: `{bundle.media_metadata.get('fps')}`",
        f"- Video codec: `{bundle.media_metadata.get('video_codec')}`",
        f"- Audio codec: `{bundle.media_metadata.get('audio_codec')}`",
        f"- SHA-256: `{bundle.media_metadata.get('sha256')}`",
        "",
        "## Structured Warnings",
        "",
    ]
    if bundle.warnings:
        for item in bundle.warnings:
            subsystem = f" `{item.get('subsystem')}`" if item.get("subsystem") else ""
            lines.append(f"- `{item.get('code')}`{subsystem}: {item.get('message')}")
    else:
        lines.append("- No structured warnings emitted.")

    lines.extend([
        "",
        "## Transcript Summary",
        "",
        f"- Status: `{bundle.transcript.get('transcription_status')}`",
        f"- Word count: `{bundle.audio_features.get('word_count')}`",
        f"- Overall WPM: `{bundle.audio_features.get('overall_words_per_minute')}`",
        "",
        "### Transcript Excerpt",
        "",
        excerpt or "[No transcript text available.]",
        "",
        "## Segment Table",
        "",
        _segment_table(bundle.scene_segments.get("segments", [])),
        "",
        "## Emotional Arc Summary",
        "",
    ])
    for segment in bundle.emotional_arc.get("segments", [])[:20]:
        lines.append(
            f"- {segment.get('segment_id')}: tone `{segment.get('dominant_tone')}`, "
            f"energy {segment.get('energy')}, valence {segment.get('valence')}, "
            f"certainty {segment.get('certainty')}, intensity {segment.get('intensity')}"
        )

    lines.extend(["", "## Persona/Style Profile", ""])
    lines.extend(_profile_lines(bundle.persona_profile))
    lines.extend(["", "## Teaching/Communication Style", ""])
    lines.extend(_profile_lines(bundle.teaching_profile))
    lines.extend(["", "## Acoustic Evidence Summary", ""])
    acoustic = bundle.acoustic_features or {}
    lines.append(f"- Status: `{acoustic.get('analysis_status')}`")
    lines.append(f"- Silence ratio: `{acoustic.get('silence_ratio')}`")
    lines.append(f"- Energy trend: `{(acoustic.get('loudness_energy_trend') or {}).get('direction')}`")
    lines.extend(["", "## Topic Analysis Summary", ""])
    topic = bundle.topic_analysis or {}
    lines.append(f"- Status: `{topic.get('analysis_status')}`")
    lines.append(f"- Topic drift score: `{topic.get('topic_drift_score')}`")
    labels = topic.get("top_global_keywords") or topic.get("tfidf_weighted_terms") or []
    lines.append("- Top terms: " + (", ".join(str(item.get("term")) for item in labels[:10]) or "limited evidence"))
    lines.extend(["", "## Rhetorical Deep Dive Summary", ""])
    rhetoric = bundle.rhetorical_analysis or {}
    lines.append(f"- Status: `{rhetoric.get('analysis_status')}`")
    lines.append(f"- Rhetorical balance score: `{rhetoric.get('rhetorical_balance_score')}`")
    discourse = bundle.discourse_summary or {}
    lines.extend(["", "## Discourse / Argument Summary", ""])
    lines.append("Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.")
    lines.append(f"- Ambiguity-adjusted continuity: `{discourse.get('ambiguity_adjusted_continuity')}`")
    lines.append(f"- Argument completeness: `{discourse.get('argument_completeness_score')}`")
    lines.append(f"- Callback resolution quality: `{discourse.get('callback_resolution_quality')}`")
    lines.append(f"- Unresolved discourse pressure: `{discourse.get('unresolved_discourse_pressure')}`")
    lines.extend(["", "## Recommendations", "", bundle.recommendations_md, "", "## Questions For A Future LLM Reviewer", ""])
    lines.append("- Which segments should be cut, expanded, or reordered for clarity?")
    lines.append("- Does the communication style match the intended audience and purpose?")
    lines.append("- Where would stronger evidence, examples, or visual variation improve retention?")
    lines.append("- Which claims need fact-checking or source support?")
    (bundle.output_dir / "llm_context_bundle.md").write_text("\n".join(lines), encoding="utf-8")


def _append_revision_context(bundle: AnalysisBundle, llm_json: dict, revision_data: dict) -> None:
    if revision_data.get("status") == "skipped":
        llm_json["revision_graph"] = revision_data
        _write_json(bundle.output_dir / "llm_context_bundle.json", llm_json)
        return
    summary = {
        "status": revision_data.get("status"),
        "root_revision_id": revision_data.get("root_revision_id"),
        "recommended_branch": revision_data.get("revision_recommendations", {}).get("recommended_branch"),
        "release_readiness_class": revision_data.get("release_readiness", {}).get("release_readiness_class"),
        "release_readiness_score": revision_data.get("release_readiness", {}).get("release_readiness_score"),
        "mutation_safety_status": revision_data.get("mutation_safety_contract", {}).get("overall_status"),
        "candidate_count": len(revision_data.get("revision_candidates", [])),
        "warning": "Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness.",
    }
    llm_json["revision_graph"] = summary
    _write_json(bundle.output_dir / "llm_context_bundle.json", llm_json)

    md_path = bundle.output_dir / "llm_context_bundle.md"
    existing = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    lines = [
        "",
        "## Revision Intelligence",
        "",
        summary["warning"],
        "",
        f"- Root revision: `{summary['root_revision_id']}`",
        f"- Recommended branch: `{summary['recommended_branch']}`",
        f"- Release readiness class: `{summary['release_readiness_class']}`",
        f"- Release readiness score: `{summary['release_readiness_score']}`",
        f"- Mutation safety status: `{summary['mutation_safety_status']}`",
        "",
    ]
    md_path.write_text(existing.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")


def _write_charts(bundle: AnalysisBundle) -> None:
    charts_dir = bundle.output_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    with (charts_dir / "emotional_arc.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["segment_id", "start_sec", "end_sec", "energy", "valence", "certainty", "intensity", "dominant_tone"],
        )
        writer.writeheader()
        for row in bundle.emotional_arc.get("segments", []):
            writer.writerow({field: row.get(field) for field in writer.fieldnames})

    with (charts_dir / "pacing_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["segment_index", "start_sec", "end_sec", "duration_sec", "word_count", "words_per_minute"])
        writer.writeheader()
        for row in bundle.audio_features.get("segment_speech_rate", []):
            writer.writerow({field: row.get(field) for field in writer.fieldnames})


def _write_continuity_outputs(bundle: AnalysisBundle) -> None:
    continuity_dir = bundle.output_dir / "continuity"
    reports_dir = bundle.output_dir / "reports"
    continuity_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    topic = bundle.topic_continuity or {}
    rhetoric = bundle.rhetorical_coherence or {}
    boundary = bundle.boundary_diagnostics or {}
    _write_json(continuity_dir / "topic_continuity.json", topic)
    _write_json(continuity_dir / "rhetorical_coherence.json", rhetoric)
    _write_json(continuity_dir / "boundary_diagnostics.json", boundary)
    summary = {
        "analysis_status": "complete" if topic or rhetoric or boundary else "limited",
        "topic_continuity_score": topic.get("topic_continuity_score"),
        "rhetorical_coherence_score": rhetoric.get("rhetorical_coherence_score"),
        "boundary_diagnostic_quality": (boundary.get("summary") or {}).get("mean_consensus_support"),
        "unsupported_shift_count": len(topic.get("unsupported_topic_shifts") or []),
        "unresolved_question_count": len(rhetoric.get("unresolved_questions") or []),
        "boundary_review_count": (boundary.get("summary") or {}).get("likely_review_boundary_count"),
        "limitations": [
            "Topic continuity and rhetorical coherence are deterministic local heuristics for editorial review.",
            "They are not semantic truth guarantees.",
        ],
    }
    _write_json(continuity_dir / "continuity_summary.json", summary)
    (reports_dir / "topic_continuity_report.md").write_text(
        "\n".join(
            [
                "# Topic Continuity Report",
                "",
                "Deterministic local transcript-window continuity evidence for human review.",
                "",
                f"- Topic continuity score: `{topic.get('topic_continuity_score')}`",
                f"- Unsupported shifts: `{len(topic.get('unsupported_topic_shifts') or [])}`",
                f"- Re-entry points: `{len(topic.get('topic_reentry_points') or [])}`",
                f"- Explanation: {topic.get('topic_drift_explanation')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (reports_dir / "rhetorical_coherence_report.md").write_text(
        "\n".join(
            [
                "# Rhetorical Coherence Report",
                "",
                "Deterministic marker-based rhetorical coherence evidence for human review.",
                "",
                f"- Rhetorical coherence score: `{rhetoric.get('rhetorical_coherence_score')}`",
                f"- Unresolved questions: `{len(rhetoric.get('unresolved_questions') or [])}`",
                f"- Claims without examples: `{len(rhetoric.get('claims_without_examples') or [])}`",
                f"- Examples without takeaways: `{len(rhetoric.get('examples_without_takeaways') or [])}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (reports_dir / "boundary_diagnostics_report.md").write_text(
        "\n".join(
            [
                "# Boundary Diagnostics Report",
                "",
                "Boundary diagnostics are review evidence only; no boundaries are rewritten automatically.",
                "",
                f"- Boundaries: `{(boundary.get('summary') or {}).get('boundary_count')}`",
                f"- Likely good: `{(boundary.get('summary') or {}).get('likely_good_boundary_count')}`",
                f"- Needs review: `{(boundary.get('summary') or {}).get('likely_review_boundary_count')}`",
                f"- Total contradictions: `{(boundary.get('summary') or {}).get('total_contradictions')}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _ensure_discourse_outputs(bundle: AnalysisBundle) -> None:
    if bundle.discourse_state is None:
        bundle.discourse_state = analyze_discourse_state(
            bundle.transcript,
            bundle.scene_segments,
            bundle.topic_analysis or {},
            bundle.rhetorical_analysis or {},
            bundle.topic_continuity or {},
            bundle.rhetorical_coherence or {},
        )
    if bundle.argument_graph is None:
        bundle.argument_graph = build_argument_graph(bundle.scene_segments, bundle.rhetorical_coherence or {}, bundle.topic_continuity or {})
    if bundle.narrative_memory is None:
        bundle.narrative_memory = analyze_narrative_memory(bundle.scene_segments, bundle.discourse_state or {}, bundle.argument_graph or {}, bundle.topic_continuity or {})
    if bundle.callback_resolution is None:
        bundle.callback_resolution = analyze_callback_resolution(bundle.scene_segments, bundle.discourse_state or {}, bundle.rhetorical_coherence or {}, bundle.narrative_memory or {})
    if bundle.editorial_ambiguity is None:
        bundle.editorial_ambiguity = analyze_editorial_ambiguity(
            bundle.scene_segments,
            bundle.topic_continuity or {},
            bundle.rhetorical_coherence or {},
            bundle.discourse_state or {},
            bundle.argument_graph or {},
            bundle.narrative_memory or {},
            bundle.callback_resolution or {},
        )
    bundle.discourse_summary = build_discourse_summary(
        bundle.scene_segments,
        bundle.topic_continuity or {},
        bundle.rhetorical_coherence or {},
        bundle.discourse_state or {},
        bundle.argument_graph or {},
        bundle.narrative_memory or {},
        bundle.callback_resolution or {},
        bundle.editorial_ambiguity or {},
        bundle.audio_features,
        bundle.emotional_arc,
    )


def _write_discourse_outputs(bundle: AnalysisBundle) -> None:
    _ensure_discourse_outputs(bundle)
    discourse_dir = bundle.output_dir / "discourse"
    reports_dir = bundle.output_dir / "reports"
    discourse_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    artifacts = {
        "discourse_state.json": bundle.discourse_state or {},
        "argument_graph.json": bundle.argument_graph or {},
        "narrative_memory.json": bundle.narrative_memory or {},
        "callback_resolution.json": bundle.callback_resolution or {},
        "editorial_ambiguity.json": bundle.editorial_ambiguity or {},
        "discourse_summary.json": bundle.discourse_summary or {},
    }
    for filename, data in artifacts.items():
        _write_json(discourse_dir / filename, data)
    report_specs = [
        ("discourse_state_report.md", "Discourse State", bundle.discourse_state, [("Discourse pressure", "discourse_pressure_score"), ("Discourse continuity", "discourse_continuity_score")]),
        ("argument_graph_report.md", "Argument Graph", bundle.argument_graph, [("Argument completeness", "argument_completeness_score"), ("Argument fragmentation", "argument_fragmentation_score")]),
        ("narrative_memory_report.md", "Narrative Memory", bundle.narrative_memory, [("Thematic persistence", "thematic_persistence_score"), ("Narrative drift", "narrative_drift_score"), ("Narrative recovery", "narrative_recovery_score")]),
        ("callback_resolution_report.md", "Callback Resolution", bundle.callback_resolution, [("Callback strength", "callback_strength_score"), ("Payoff quality", "payoff_quality_score")]),
        ("editorial_ambiguity_report.md", "Editorial Ambiguity", bundle.editorial_ambiguity, [("Ambiguity confidence", "ambiguity_confidence_score")]),
    ]
    for filename, title, data, metrics in report_specs:
        lines = [
            f"# {title} Report",
            "",
            "Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.",
            "",
        ]
        for label, key in metrics:
            lines.append(f"- {label}: `{(data or {}).get(key)}`")
        if title == "Editorial Ambiguity":
            lines.append(f"- Ambiguity regions: `{len((data or {}).get('ambiguity_regions') or [])}`")
        if title == "Argument Graph":
            lines.append(f"- Unresolved chains: `{len((data or {}).get('unresolved_chains') or [])}`")
        if title == "Callback Resolution":
            lines.append(f"- Unresolved setups: `{len((data or {}).get('unresolved_setups') or [])}`")
        lines.extend(["", "## Limitations", ""])
        lines.extend(f"- {item}" for item in (data or {}).get("limitations", []))
        (reports_dir / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_discourse_outputs(bundle: AnalysisBundle) -> None:
    schema_dir = bundle.schema_path.parent
    _ensure_discourse_outputs(bundle)
    rows = []
    for artifact, data, schema_name in [
        ("discourse/discourse_state.json", bundle.discourse_state or {}, "discourse_state.schema.json"),
        ("discourse/argument_graph.json", bundle.argument_graph or {}, "argument_graph.schema.json"),
        ("discourse/narrative_memory.json", bundle.narrative_memory or {}, "narrative_memory.schema.json"),
        ("discourse/callback_resolution.json", bundle.callback_resolution or {}, "callback_resolution.schema.json"),
        ("discourse/editorial_ambiguity.json", bundle.editorial_ambiguity or {}, "editorial_ambiguity.schema.json"),
    ]:
        schema_path = schema_dir / schema_name
        report = validate_against_schema(data, schema_path)
        rows.append({"artifact": artifact, **report})
    node_ids = {row.get("node_id") for row in (bundle.argument_graph or {}).get("nodes", [])}
    custom_errors = []
    for index, edge in enumerate((bundle.argument_graph or {}).get("edges", [])):
        if edge.get("from_node_id") not in node_ids:
            custom_errors.append({"path": f"$.argument_graph.edges[{index}].from_node_id", "message": "Edge references missing from_node_id."})
        if edge.get("to_node_id") not in node_ids:
            custom_errors.append({"path": f"$.argument_graph.edges[{index}].to_node_id", "message": "Edge references missing to_node_id."})
    if custom_errors:
        rows.append({"artifact": "discourse/argument_graph.json", "validation_status": STATUS_ERROR, "error_count": len(custom_errors), "errors": custom_errors})
    output = {
        "validation_status": STATUS_COMPLETE if all(row.get("validation_status") == STATUS_COMPLETE for row in rows) else STATUS_ERROR,
        "error_count": sum(int(row.get("error_count") or 0) for row in rows),
        "results": rows,
        "limitations": [
            "Discourse validation checks required fields and core deterministic reference integrity.",
            "Validation is local and standalone.",
        ],
    }
    _write_json(bundle.evidence_dir / "discourse_schema_validation.json", output)


def _validate_continuity_outputs(bundle: AnalysisBundle) -> None:
    schema_dir = bundle.schema_path.parent
    rows = []
    for artifact, data, schema_name in [
        ("continuity/topic_continuity.json", bundle.topic_continuity or {}, "topic_continuity.schema.json"),
        ("continuity/rhetorical_coherence.json", bundle.rhetorical_coherence or {}, "rhetorical_coherence.schema.json"),
        ("continuity/boundary_diagnostics.json", bundle.boundary_diagnostics or {}, "boundary_diagnostics.schema.json"),
    ]:
        schema_path = schema_dir / schema_name
        report = validate_against_schema(data, schema_path)
        rows.append({"artifact": artifact, **report})
    output = {
        "validation_status": STATUS_COMPLETE if all(row.get("validation_status") == STATUS_COMPLETE for row in rows) else STATUS_ERROR,
        "error_count": sum(int(row.get("error_count") or 0) for row in rows),
        "results": rows,
    }
    _write_json(bundle.evidence_dir / "continuity_schema_validation.json", output)


def _combined_status(statuses: list[str]) -> str:
    normalized = [normalize_status(status) for status in statuses]
    if any(status == STATUS_ERROR for status in normalized):
        return STATUS_ERROR
    if any(status == STATUS_UNAVAILABLE for status in normalized):
        return STATUS_UNAVAILABLE
    if any(status == STATUS_LIMITED for status in normalized):
        return STATUS_LIMITED
    if any(status == STATUS_SKIPPED for status in normalized):
        return STATUS_SKIPPED
    return STATUS_COMPLETE


def _limitations(bundle: AnalysisBundle) -> list[str]:
    limitations: list[str] = []
    for source in (
        bundle.scene_segments,
        bundle.emotional_arc,
        bundle.audio_features,
        bundle.visual_index,
        bundle.persona_profile,
        bundle.teaching_profile,
        bundle.acoustic_features or {},
        bundle.topic_analysis or {},
        bundle.rhetorical_analysis or {},
        bundle.topic_continuity or {},
        bundle.rhetorical_coherence or {},
        bundle.discourse_state or {},
        bundle.argument_graph or {},
        bundle.narrative_memory or {},
        bundle.callback_resolution or {},
        bundle.editorial_ambiguity or {},
        bundle.discourse_summary or {},
        bundle.visual_structure or {},
        bundle.shot_boundaries or {},
        bundle.visual_continuity or {},
        bundle.composition_features or {},
        bundle.visual_boundary_alignment or {},
        (bundle.sequence_outputs or {}).get("sequence_summary", {}),
        (bundle.comparative_outputs or {}).get("comparative_summary", {}),
        bundle.recommendations_json or {},
    ):
        value = source.get("limitations")
        if isinstance(value, list):
            limitations.extend(str(item) for item in value)
        elif value:
            limitations.append(str(value))
    limitations.append("All acoustic, rhetorical, persona, emotional, topic, discourse, and visual outputs are heuristic evidence summaries for human review. They are not psychological, clinical, identity, object, emotion, or intent claims.")
    return sorted(dict.fromkeys(limitations))


def _build_llm_json(bundle: AnalysisBundle, generated_at: str) -> dict:
    return {
        "generated_at_utc": generated_at,
        "tool_version": TOOL_VERSION,
        "source_video": bundle.source_video,
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "analysis_profile_hash": bundle.profile_hash,
        "media_metadata": bundle.media_metadata,
        "transcript": bundle.transcript,
        "audio_features": bundle.audio_features,
        "visual_sample_index": bundle.visual_index,
        "scene_segments": bundle.scene_segments,
        "emotional_arc": bundle.emotional_arc,
        "acoustic_features": bundle.acoustic_features or {},
        "topic_analysis": bundle.topic_analysis or {},
        "rhetorical_analysis": bundle.rhetorical_analysis or {},
        "topic_continuity": bundle.topic_continuity or {},
        "rhetorical_coherence": bundle.rhetorical_coherence or {},
        "boundary_diagnostics": bundle.boundary_diagnostics or {},
        "discourse_state": bundle.discourse_state or {},
        "argument_graph": bundle.argument_graph or {},
        "narrative_memory": bundle.narrative_memory or {},
        "callback_resolution": bundle.callback_resolution or {},
        "editorial_ambiguity": bundle.editorial_ambiguity or {},
        "discourse_summary": bundle.discourse_summary or {},
        "visual_structure": bundle.visual_structure or {},
        "shot_boundaries": bundle.shot_boundaries or {},
        "visual_continuity": bundle.visual_continuity or {},
        "composition_features": bundle.composition_features or {},
        "visual_boundary_alignment": bundle.visual_boundary_alignment or {},
        "sequence_intelligence": bundle.sequence_outputs or {},
        "comparative_intelligence": bundle.comparative_outputs or {},
        "persona_style_profile": bundle.persona_profile,
        "teaching_style_profile": bundle.teaching_profile,
        "recommendations": bundle.recommendations_json or {},
        "consensus": _consensus_context(bundle.consensus_outputs or {}),
        "recommendations_markdown": bundle.recommendations_md,
        "warnings": bundle.warnings,
        "limitations": _limitations(bundle),
        "analysis_profile": bundle.profile,
    }


def _consensus_context(consensus_outputs: dict) -> dict:
    if not consensus_outputs:
        return {}
    return {
        "evidence_consensus_summary": (consensus_outputs.get("evidence_consensus") or {}).get("summary", {}),
        "transition_confidence_summary": (consensus_outputs.get("transition_confidence") or {}).get("summary", {}),
        "modality_agreement_summary": (consensus_outputs.get("modality_agreement") or {}).get("summary", {}),
        "evidence_quality": {
            "overall_evidence_strength": (consensus_outputs.get("evidence_score_summary") or {}).get("overall_evidence_strength"),
            "weakest_evidence": (consensus_outputs.get("evidence_score_summary") or {}).get("weakest_evidence", []),
        },
        "warning": "Consensus outputs are deterministic evidence-fusion heuristics for review, not semantic truth guarantees or autonomous editorial decisions.",
    }


def write_bundle(bundle: AnalysisBundle) -> dict:
    generated_at = utc_now_iso()
    if bundle.topic_continuity is None:
        bundle.topic_continuity = analyze_topic_continuity(bundle.transcript, bundle.scene_segments, bundle.topic_analysis or {})
    if bundle.rhetorical_coherence is None:
        bundle.rhetorical_coherence = analyze_rhetorical_coherence(bundle.transcript, bundle.scene_segments, bundle.rhetorical_analysis or {})
    _ensure_discourse_outputs(bundle)
    llm_json = _build_llm_json(bundle, generated_at)
    validation_report = validate_against_schema(llm_json, bundle.schema_path)
    if validation_report.get("validation_status") != STATUS_COMPLETE:
        bundle.warnings.append(
            warning(
                "SCHEMA_VALIDATION_FAILED",
                f"Bundle schema validation reported {validation_report.get('error_count')} error(s).",
                "error",
                "bundle_generation",
            )
        )
        llm_json["warnings"] = bundle.warnings
    write_validation_report(validation_report, bundle.output_dir, bundle.evidence_dir)

    subsystem_statuses = {
        "media_probe": normalize_status(bundle.media_metadata.get("probe_status")),
        "audio_extract": normalize_status(bundle.audio_result.get("status")),
        "transcription": normalize_status(bundle.transcript.get("transcription_status")),
        "segmentation": normalize_status(bundle.scene_segments.get("segmentation_status")),
        "emotional_arc": normalize_status(bundle.emotional_arc.get("analysis_status")),
        "persona_classification": _combined_status(
            [
                bundle.persona_profile.get("classification_status"),
                bundle.teaching_profile.get("classification_status"),
            ]
        ),
        "acoustic_analysis": normalize_status((bundle.acoustic_features or {}).get("analysis_status")),
        "topic_analysis": normalize_status((bundle.topic_analysis or {}).get("analysis_status")),
        "rhetorical_analysis": normalize_status((bundle.rhetorical_analysis or {}).get("analysis_status")),
        "discourse_state": normalize_status((bundle.discourse_state or {}).get("analysis_status")),
        "argument_graph": normalize_status((bundle.argument_graph or {}).get("analysis_status")),
        "narrative_memory": normalize_status((bundle.narrative_memory or {}).get("analysis_status")),
        "callback_resolution": normalize_status((bundle.callback_resolution or {}).get("analysis_status")),
        "editorial_ambiguity": normalize_status((bundle.editorial_ambiguity or {}).get("analysis_status")),
        "visual_sampling": normalize_status(bundle.visual_index.get("sampling_status")),
        "visual_structure": normalize_status((bundle.visual_structure or {}).get("analysis_status")),
        "bundle_generation": STATUS_COMPLETE if validation_report.get("validation_status") == STATUS_COMPLETE else STATUS_LIMITED,
    }

    manifest = {
        "bundle_version": TOOL_VERSION,
        "tool_version": TOOL_VERSION,
        "generated_at_utc": generated_at,
        "generation_timestamp_utc": generated_at,
        "source_video": bundle.source_video,
        "source_video_sha256": bundle.media_metadata.get("sha256"),
        "source_video_size_bytes": bundle.media_metadata.get("file_size_bytes"),
        "analysis_profile": bundle.profile_path,
        "analysis_profile_hash": bundle.profile_hash,
        "output_dir": str(bundle.output_dir),
        "dependency_versions": dependency_versions(bundle.dependency_report),
        "execution_duration_sec": round(bundle.execution_duration_sec, 3),
        "warnings": bundle.warnings,
        "limitations": _limitations(bundle),
        "artifacts": {
            "manifest": "manifest.json",
            "dependency_report": "dependency_report.json",
            "validation_report": "validation_report.json",
            "transcript_json": "transcript.json",
            "transcript_srt": "transcript.srt",
            "audio_features": "audio_features.json",
            "acoustic_features": "acoustic_features.json",
            "topic_analysis": "topic_analysis.json",
            "rhetorical_analysis": "rhetorical_analysis.json",
            "visual_sample_index": "visual_sample_index.json",
            "scene_segments": "scene_segments.json",
            "emotional_arc": "emotional_arc.json",
            "persona_style_profile": "persona_style_profile.json",
            "teaching_style_profile": "teaching_style_profile.json",
            "recommendations": "recommendations.md",
            "recommendations_json": "recommendations.json",
            "llm_context_bundle_md": "llm_context_bundle.md",
            "llm_context_bundle_json": "llm_context_bundle.json",
            "analysis_index_json": "analysis_index.json",
            "analysis_index_md": "analysis_index.md",
            "charts": "charts/",
            "frames": "frames/",
            "verification_evidence": "verification_evidence/",
            "revision_graph": "revision_graph/",
            "consensus": "consensus/",
            "discourse": "discourse/",
            "visual_structure": "visual_structure/",
            "sequence": "sequence/",
            "comparative": "comparative/",
        },
        "subsystem_statuses": subsystem_statuses,
        "statuses": subsystem_statuses,
        "schema_validation_status": validation_report.get("validation_status"),
    }

    _write_json(bundle.output_dir / "manifest.json", manifest)
    _write_json(bundle.output_dir / "llm_context_bundle.json", llm_json)
    _write_markdown_bundle(bundle)
    _write_charts(bundle)
    consensus_outputs = build_evidence_consensus(bundle)
    bundle.consensus_outputs = consensus_outputs
    bundle.boundary_diagnostics = analyze_boundary_diagnostics(
        bundle.scene_segments,
        bundle.audio_features,
        bundle.acoustic_features or {},
        bundle.topic_continuity or {},
        bundle.rhetorical_coherence or {},
        bundle.emotional_arc,
        consensus_outputs.get("transition_confidence") or {},
        bundle.discourse_state or {},
        bundle.argument_graph or {},
        bundle.narrative_memory or {},
        bundle.callback_resolution or {},
        bundle.editorial_ambiguity or {},
        bundle.visual_boundary_alignment or {},
    )
    bundle.scene_segments = attach_boundary_diagnostics(bundle.scene_segments, bundle.boundary_diagnostics)
    _write_json(bundle.output_dir / "scene_segments.json", bundle.scene_segments)
    _write_continuity_outputs(bundle)
    _validate_continuity_outputs(bundle)
    _write_discourse_outputs(bundle)
    _validate_discourse_outputs(bundle)
    write_consensus_outputs(bundle, consensus_outputs)
    visual_outputs = build_visual_structure_outputs(bundle)
    bundle.visual_structure = visual_outputs.get("visual_structure")
    bundle.shot_boundaries = visual_outputs.get("shot_boundaries")
    bundle.visual_continuity = visual_outputs.get("visual_continuity")
    bundle.composition_features = visual_outputs.get("composition_features")
    bundle.visual_boundary_alignment = visual_outputs.get("visual_boundary_alignment")
    consensus_outputs = build_evidence_consensus(bundle)
    bundle.consensus_outputs = consensus_outputs
    bundle.boundary_diagnostics = analyze_boundary_diagnostics(
        bundle.scene_segments,
        bundle.audio_features,
        bundle.acoustic_features or {},
        bundle.topic_continuity or {},
        bundle.rhetorical_coherence or {},
        bundle.emotional_arc,
        consensus_outputs.get("transition_confidence") or {},
        bundle.discourse_state or {},
        bundle.argument_graph or {},
        bundle.narrative_memory or {},
        bundle.callback_resolution or {},
        bundle.editorial_ambiguity or {},
        bundle.visual_boundary_alignment or {},
    )
    bundle.scene_segments = attach_boundary_diagnostics(bundle.scene_segments, bundle.boundary_diagnostics)
    _write_json(bundle.output_dir / "scene_segments.json", bundle.scene_segments)
    _write_continuity_outputs(bundle)
    _validate_continuity_outputs(bundle)
    write_consensus_outputs(bundle, consensus_outputs)
    enriched_recommendations = enrich_recommendations_with_consensus(bundle.recommendations_json or {}, consensus_outputs)
    enriched_recommendations = enrich_recommendations_with_discourse(enriched_recommendations, bundle)
    enriched_recommendations = enrich_recommendations_with_visual(enriched_recommendations, bundle)
    bundle.recommendations_json = enriched_recommendations
    bundle.recommendations_md = enriched_recommendations.get("markdown", bundle.recommendations_md)
    _write_json(bundle.output_dir / "recommendations.json", {k: v for k, v in enriched_recommendations.items() if k != "markdown"})
    (bundle.output_dir / "recommendations.md").write_text(bundle.recommendations_md, encoding="utf-8")
    llm_json = _build_llm_json(bundle, generated_at)
    _write_json(bundle.output_dir / "llm_context_bundle.json", llm_json)
    _write_markdown_bundle(bundle)
    report_data = write_reports(bundle)
    if bundle.enable_revision_graph:
        revision_data = build_revision_graph(bundle, report_data, bundle.revision_profile)
    else:
        revision_data = write_disabled_revision_status(bundle.output_dir, "--no-revision-graph was supplied.")
        bundle.warnings.append(
            warning(
                "REVISION_GRAPH_SKIPPED",
                "Deterministic editorial revision graph generation was disabled.",
                "warning",
                "revision_graph",
            )
        )
        llm_json["warnings"] = bundle.warnings
    consensus_outputs["evidence_score_summary"] = build_evidence_score_summary(bundle, consensus_outputs.get("transition_confidence"), revision_data)
    bundle.consensus_outputs = consensus_outputs
    bundle.boundary_diagnostics = analyze_boundary_diagnostics(
        bundle.scene_segments,
        bundle.audio_features,
        bundle.acoustic_features or {},
        bundle.topic_continuity or {},
        bundle.rhetorical_coherence or {},
        bundle.emotional_arc,
        consensus_outputs.get("transition_confidence") or {},
        bundle.discourse_state or {},
        bundle.argument_graph or {},
        bundle.narrative_memory or {},
        bundle.callback_resolution or {},
        bundle.editorial_ambiguity or {},
        bundle.visual_boundary_alignment or {},
    )
    bundle.scene_segments = attach_boundary_diagnostics(bundle.scene_segments, bundle.boundary_diagnostics)
    _write_json(bundle.output_dir / "scene_segments.json", bundle.scene_segments)
    _write_continuity_outputs(bundle)
    _validate_continuity_outputs(bundle)
    _write_discourse_outputs(bundle)
    _validate_discourse_outputs(bundle)
    write_consensus_outputs(bundle, consensus_outputs)
    llm_json = _build_llm_json(bundle, generated_at)
    _append_revision_context(bundle, llm_json, revision_data)
    revision_schema_validation = validate_revision_artifacts(bundle.output_dir, bundle.schema_path.parent)
    bundle.sequence_outputs = write_sequence_outputs(bundle)
    bundle.comparative_outputs = write_comparative_outputs(bundle.output_dir, bundle.schema_path.parent, [bundle.output_dir])
    llm_json = _build_llm_json(bundle, generated_at)
    _append_revision_context(bundle, llm_json, revision_data)
    manifest["revision_schema_validation_status"] = revision_schema_validation.get("validation_status")
    manifest["consensus_validation_status"] = "complete" if not any(
        row.get("validation_status") != STATUS_COMPLETE
        for row in revision_schema_validation.get("results", [])
        if str(row.get("artifact", "")).startswith("consensus/")
    ) else "error"
    graph_status = build_graphs(bundle, report_data)
    _ensure_history_placeholders(bundle.output_dir)
    visualization_status = write_visualizations(bundle, report_data, graph_status)
    index_data = write_analysis_index(bundle, manifest, report_data, graph_status, visualization_status)
    _clear_regenerated_history_reports(bundle.output_dir)
    _ensure_history_placeholders(bundle.output_dir)
    integrity_outputs = run_integrity_suite(bundle.output_dir, bundle.schema_path.parent)
    manifest["artifacts"].update(
        {
            "visualizations": "visualizations/",
            "dashboard": "visualizations/dashboard.html",
            "transcript_explorer": "visualizations/transcript_explorer.html",
            "graphs": "graphs/",
            "reports": "reports/",
            "quality_report_md": "reports/quality_report.md",
            "quality_report_json": "reports/quality_report.json",
            "acoustic_statistics": "reports/acoustic_statistics.json",
            "topic_statistics": "reports/topic_statistics.json",
            "rhetorical_deep_dive": "reports/rhetorical_deep_dive.json",
            "segment_boundary_report": "reports/segment_boundary_report.json",
            "analysis_index_json": "analysis_index.json",
            "analysis_index_md": "analysis_index.md",
            "revision_graph_json": "revision_graph/revision_graph.json",
            "revision_states": "revision_graph/revision_states.json",
            "revision_lineage": "revision_graph/revision_lineage.json",
            "revision_candidates": "revision_graph/revision_candidates.json",
            "revision_deltas": "revision_graph/revision_deltas.json",
            "editorial_constraints": "revision_graph/editorial_constraints.json",
            "release_readiness_report": "revision_graph/release_readiness_report.json",
            "mutation_safety_contract": "revision_graph/mutation_safety_contract.json",
            "branch_comparison_report": "revision_graph/branch_comparison_report.json",
            "revision_recommendations": "revision_graph/revision_recommendations.json",
            "evidence_consensus": "consensus/evidence_consensus.json",
            "modality_agreement": "consensus/modality_agreement.json",
            "modality_disagreement": "consensus/modality_disagreement.json",
            "transition_confidence": "consensus/transition_confidence.json",
            "evidence_score_summary": "consensus/evidence_score_summary.json",
            "false_positive_boundaries": "consensus/false_positive_boundaries.json",
            "continuity_analysis": "consensus/continuity_analysis.json",
            "continuity": "continuity/",
            "topic_continuity": "continuity/topic_continuity.json",
            "rhetorical_coherence": "continuity/rhetorical_coherence.json",
            "boundary_diagnostics": "continuity/boundary_diagnostics.json",
            "continuity_schema_validation": "verification_evidence/continuity_schema_validation.json",
            "discourse_state": "discourse/discourse_state.json",
            "argument_graph": "discourse/argument_graph.json",
            "narrative_memory": "discourse/narrative_memory.json",
            "callback_resolution": "discourse/callback_resolution.json",
            "editorial_ambiguity": "discourse/editorial_ambiguity.json",
            "discourse_summary": "discourse/discourse_summary.json",
            "discourse_schema_validation": "verification_evidence/discourse_schema_validation.json",
            "revision_schema_validation": "verification_evidence/revision_schema_validation.json",
            "consensus_validation": "verification_evidence/consensus_validation.json",
            "visual_structure": "visual_structure/visual_structure.json",
            "shot_boundaries": "visual_structure/shot_boundaries.json",
            "visual_continuity_visual": "visual_structure/visual_continuity.json",
            "composition_features": "visual_structure/composition_features.json",
            "visual_boundary_alignment": "visual_structure/visual_boundary_alignment.json",
            "visual_structure_summary": "visual_structure/visual_structure_summary.json",
            "visual_structure_validation": "verification_evidence/visual_structure_validation.json",
            "integrity": "integrity/",
            "artifact_integrity": "integrity/artifact_integrity.json",
            "graph_consistency": "integrity/graph_consistency.json",
            "reference_validation": "integrity/reference_validation.json",
            "lineage_validation": "integrity/lineage_validation.json",
            "dashboard_coverage": "integrity/dashboard_coverage.json",
            "migration_registry": "integrity/migration_registry.json",
            "semantic_readiness": "integrity/semantic_readiness.json",
            "integrity_validation": "verification_evidence/integrity_validation.json",
            "graph_validation": "verification_evidence/graph_validation.json",
            "migration_validation": "verification_evidence/migration_validation.json",
            "history": "history/",
            "run_history": "history/run_history.json",
            "run_snapshots": "history/run_snapshots.json",
            "run_comparison": "history/run_comparison.json",
            "artifact_drift_report": "history/artifact_drift_report.json",
            "metric_drift_report": "history/metric_drift_report.json",
            "schema_version_diff": "history/schema_version_diff.json",
            "dependency_drift_report": "history/dependency_drift_report.json",
            "readiness_drift_report": "history/readiness_drift_report.json",
            "history_validation": "verification_evidence/history_validation.json",
            "sequence": "sequence/",
            "sequence_summary": "sequence/sequence_summary.json",
            "sequence_structure": "sequence/sequence_structure.json",
            "scene_hierarchy": "sequence/scene_hierarchy.json",
            "temporal_rhythm": "sequence/temporal_rhythm.json",
            "narrative_phase_model": "sequence/narrative_phase_model.json",
            "editorial_pressure": "sequence/editorial_pressure.json",
            "recommendation_dependencies_sequence": "sequence/recommendation_dependencies.json",
            "revision_propagation_sequence": "sequence/revision_propagation.json",
            "counterfactual_simulation": "sequence/counterfactual_simulation.json",
            "revision_forecasting": "sequence/revision_forecasting.json",
            "epistemic_stability": "sequence/epistemic_stability.json",
            "temporal_structure_validation": "verification_evidence/temporal_structure_validation.json",
            "revision_simulation_validation": "verification_evidence/revision_simulation_validation.json",
            "comparative": "comparative/",
            "comparative_summary": "comparative/comparative_summary.json",
            "multi_video_analysis": "comparative/multi_video_analysis.json",
            "style_fingerprint": "comparative/style_fingerprint.json",
            "rhetorical_fingerprint": "comparative/rhetorical_fingerprint.json",
            "pacing_fingerprint": "comparative/pacing_fingerprint.json",
            "discourse_fingerprint": "comparative/discourse_fingerprint.json",
            "creator_evolution": "comparative/creator_evolution.json",
            "structural_pattern_mining": "comparative/structural_pattern_mining.json",
            "comparative_recommendations": "comparative/comparative_recommendations.json",
            "semantic_equivalence_scaffolding": "comparative/semantic_equivalence_scaffolding.json",
            "comparative_validation": "verification_evidence/comparative_validation.json",
        }
    )
    if index_data.get("artifacts", {}).get("interactive"):
        manifest["artifacts"]["interactive"] = "interactive/"
    manifest["subsystem_statuses"]["reporting"] = visualization_status.get("status", STATUS_COMPLETE)
    manifest["subsystem_statuses"]["graphs"] = graph_status.get("status", STATUS_COMPLETE)
    manifest["subsystem_statuses"]["revision_graph"] = STATUS_COMPLETE if revision_data.get("status") == "complete" else STATUS_SKIPPED
    manifest["subsystem_statuses"]["evidence_consensus"] = STATUS_COMPLETE if consensus_outputs.get("evidence_consensus", {}).get("analysis_status") == STATUS_COMPLETE else STATUS_LIMITED
    manifest["subsystem_statuses"]["discourse"] = STATUS_COMPLETE if (bundle.discourse_summary or {}).get("analysis_status") == STATUS_COMPLETE else STATUS_LIMITED
    manifest["subsystem_statuses"]["visual_structure"] = STATUS_COMPLETE if (bundle.visual_structure or {}).get("analysis_status") == STATUS_COMPLETE else STATUS_LIMITED
    manifest["subsystem_statuses"]["sequence_intelligence"] = (bundle.sequence_outputs or {}).get("sequence_summary", {}).get("analysis_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["comparative_intelligence"] = (bundle.comparative_outputs or {}).get("comparative_summary", {}).get("analysis_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["revision_schema_validation"] = STATUS_COMPLETE if revision_schema_validation.get("validation_status") == STATUS_COMPLETE else STATUS_ERROR
    manifest["subsystem_statuses"]["artifact_integrity"] = integrity_outputs.get("artifact_integrity", {}).get("validation_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["graph_consistency"] = integrity_outputs.get("graph_consistency", {}).get("validation_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["reference_validation"] = integrity_outputs.get("reference_validation", {}).get("validation_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["lineage_validation"] = integrity_outputs.get("lineage_validation", {}).get("validation_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["semantic_readiness"] = integrity_outputs.get("semantic_readiness", {}).get("validation_status", STATUS_LIMITED)
    manifest["integrity_summary"] = {
        "artifact_integrity_score": integrity_outputs.get("artifact_integrity", {}).get("integrity_score"),
        "graph_consistency_score": integrity_outputs.get("graph_consistency", {}).get("graph_integrity_score"),
        "reference_integrity_score": integrity_outputs.get("reference_validation", {}).get("reference_integrity_score"),
        "lineage_consistency_score": integrity_outputs.get("lineage_validation", {}).get("lineage_consistency_score"),
        "dashboard_coverage_score": integrity_outputs.get("dashboard_coverage", {}).get("dashboard_coverage_score"),
    }
    current_index = write_analysis_index(bundle, manifest, report_data, graph_status, visualization_status)
    previous_snapshots = load_snapshots(bundle.output_dir)
    current_snapshot = build_run_snapshot(bundle, manifest, current_index)
    previous_snapshot = next(
        (
            row
            for row in reversed(previous_snapshots)
            if row.get("source_sha256") == current_snapshot.get("source_sha256")
        ),
        None,
    )
    comparison = compare_runs(bundle.output_dir, previous_snapshot, current_snapshot, bundle.schema_path.parent)
    write_run_history(bundle.output_dir, current_snapshot, previous_snapshots, bundle.schema_path.parent)
    longitudinal_snapshots = (previous_snapshots + [current_snapshot])[-20:]
    longitudinal_outputs = write_longitudinal_outputs(bundle.output_dir, longitudinal_snapshots, bundle.schema_path.parent)
    manifest["history_summary"] = {
        "current_run_id": current_snapshot.get("run_id"),
        "comparison_id": comparison.get("comparison_id"),
        "comparison_classification": comparison.get("classification"),
        "suspicious_drift_count": (comparison.get("drift_summary") or {}).get("suspicious_drift_count"),
        "longitudinal_status": (longitudinal_outputs.get("longitudinal_summary") or {}).get("analysis_status"),
        "longitudinal_confidence": (longitudinal_outputs.get("longitudinal_summary") or {}).get("longitudinal_confidence"),
    }
    manifest["subsystem_statuses"]["run_history"] = STATUS_COMPLETE
    manifest["subsystem_statuses"]["longitudinal_analysis"] = (longitudinal_outputs.get("longitudinal_summary") or {}).get("analysis_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["sequence_intelligence"] = (bundle.sequence_outputs or {}).get("sequence_summary", {}).get("analysis_status", STATUS_LIMITED)
    manifest["subsystem_statuses"]["comparative_intelligence"] = (bundle.comparative_outputs or {}).get("comparative_summary", {}).get("analysis_status", STATUS_LIMITED)
    manifest["artifacts"].update(
        {
            "longitudinal": "longitudinal/",
            "longitudinal_analysis": "longitudinal/longitudinal_analysis.json",
            "trend_analysis": "longitudinal/trend_analysis.json",
            "confidence_volatility": "longitudinal/confidence_volatility.json",
            "recommendation_evolution": "longitudinal/recommendation_evolution.json",
            "anomaly_clusters": "longitudinal/anomaly_clusters.json",
            "persistent_patterns": "longitudinal/persistent_patterns.json",
            "semantic_evolution": "longitudinal/semantic_evolution.json",
            "longitudinal_validation": "verification_evidence/longitudinal_validation.json",
        }
    )
    manifest["limitations"] = _limitations(bundle)
    manifest["statuses"] = manifest["subsystem_statuses"]
    _write_json(bundle.output_dir / "manifest.json", manifest)
    write_analysis_index(bundle, manifest, report_data, graph_status, visualization_status)
    return manifest
