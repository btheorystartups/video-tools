"""Portable static HTML visualization writers."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from dashboard_graph_clickthrough_repair import CORE_GRAPHS, EXTENDED_GRAPH_DETAIL_LINKS, ensure_core_detail_pages, ensure_graph_detail_index, grouped_detail_links_html
from dashboard_data_completeness import run as run_dashboard_data_completeness
from dashboard_interpretation_engine import run as run_dashboard_interpretation
from dashboard_page_enrichment import enrich_dashboard_pages
from placeholder_text_audit import run as run_placeholder_text_audit
from report_generator import MARKERS, keyword_counts

ASSET_DIR = Path(__file__).resolve().parent.parent / "static_assets"
PAGE_NAMES = [
    "dashboard.html",
    "transcript_explorer.html",
    "emotional_arc.html",
    "pacing_analysis.html",
    "persona_analysis.html",
    "rhetorical_flow.html",
    "segment_timeline.html",
    "transcript_density.html",
    "recommendations_report.html",
    "acoustic_analysis.html",
    "topic_analysis.html",
    "rhetorical_deep_dive.html",
    "segment_quality.html",
    "frame_contact_sheet.html",
    "revision_graph.html",
    "revision_comparison.html",
    "release_readiness.html",
    "mutation_safety.html",
    "editorial_evolution.html",
    "evidence_consensus.html",
    "continuity_analysis.html",
    "segmentation_confidence.html",
    "modality_alignment.html",
    "topic_continuity.html",
    "rhetorical_coherence.html",
    "boundary_diagnostics.html",
    "discourse_state.html",
    "argument_graph.html",
    "narrative_memory.html",
    "callback_resolution.html",
    "editorial_ambiguity.html",
    "visual_structure.html",
    "shot_boundaries.html",
    "visual_continuity.html",
    "composition_features.html",
    "visual_boundary_alignment.html",
    "artifact_integrity.html",
    "graph_consistency.html",
    "reference_validation.html",
    "lineage_validation.html",
    "migration_registry.html",
    "semantic_readiness.html",
    "run_history.html",
    "artifact_drift.html",
    "metric_drift.html",
    "readiness_drift.html",
    "longitudinal_analysis.html",
    "trend_analysis.html",
    "confidence_volatility.html",
    "recommendation_evolution.html",
    "anomaly_clusters.html",
    "persistent_patterns.html",
    "semantic_evolution.html",
    "sequence_structure.html",
    "temporal_rhythm.html",
    "narrative_phase_model.html",
    "editorial_pressure.html",
    "recommendation_dependencies.html",
    "revision_propagation.html",
    "counterfactual_simulation.html",
    "epistemic_stability.html",
    "multi_video_analysis.html",
    "style_fingerprint.html",
    "rhetorical_fingerprint.html",
    "pacing_fingerprint.html",
    "discourse_fingerprint.html",
    "creator_evolution.html",
    "structural_pattern_mining.html",
    "comparative_recommendations.html",
    "semantic_equivalence_scaffolding.html",
]


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def _copy_assets(output_dir: Path) -> None:
    target = output_dir / "static_assets"
    target.mkdir(exist_ok=True)
    for path in ASSET_DIR.glob("*"):
        if path.is_file():
            shutil.copyfile(path, target / path.name)


def _page(title: str, active: str, body: str) -> str:
    nav = "\n".join(
        f'<a class="{"active" if name == active else ""}" href="{name}">{label}</a>'
        for name, label in [
            ("dashboard.html", "Dashboard"),
            ("transcript_explorer.html", "Transcript Explorer"),
            ("emotional_arc.html", "Emotional Arc"),
            ("pacing_analysis.html", "Pacing"),
            ("persona_analysis.html", "Persona / Style"),
            ("rhetorical_flow.html", "Rhetorical Flow"),
            ("segment_timeline.html", "Segment Timeline"),
            ("transcript_density.html", "Transcript Density"),
            ("recommendations_report.html", "Recommendations"),
            ("acoustic_analysis.html", "Acoustic"),
            ("topic_analysis.html", "Topics"),
            ("rhetorical_deep_dive.html", "Rhetorical Deep Dive"),
            ("segment_quality.html", "Segment Quality"),
            ("frame_contact_sheet.html", "Frame Contact Sheet"),
            ("revision_graph.html", "Revision Graph"),
            ("revision_comparison.html", "Branch Comparison"),
            ("release_readiness.html", "Release Readiness"),
            ("mutation_safety.html", "Mutation Safety"),
            ("editorial_evolution.html", "Editorial Evolution"),
            ("visual_structure.html", "Visual Structure"),
            ("artifact_integrity.html", "Artifact Integrity"),
            ("graph_consistency.html", "Graph Consistency"),
            ("reference_validation.html", "Reference Validation"),
            ("migration_registry.html", "Migration Registry"),
            ("semantic_readiness.html", "Semantic Readiness"),
            ("run_history.html", "Run History"),
            ("artifact_drift.html", "Artifact Drift"),
            ("metric_drift.html", "Metric Drift"),
            ("readiness_drift.html", "Readiness Drift"),
            ("longitudinal_analysis.html", "Longitudinal Analysis"),
            ("trend_analysis.html", "Trend Analysis"),
            ("confidence_volatility.html", "Confidence Volatility"),
            ("recommendation_evolution.html", "Recommendation Evolution"),
            ("anomaly_clusters.html", "Anomaly Clusters"),
            ("persistent_patterns.html", "Persistent Patterns"),
            ("semantic_evolution.html", "Semantic Evolution"),
            ("sequence_structure.html", "Sequence Intelligence"),
            ("temporal_rhythm.html", "Temporal Rhythm"),
            ("narrative_phase_model.html", "Narrative Phase Structure"),
            ("editorial_pressure.html", "Editorial Pressure"),
            ("recommendation_dependencies.html", "Recommendation Dependencies"),
            ("revision_propagation.html", "Revision Propagation"),
            ("counterfactual_simulation.html", "Counterfactual Simulation"),
            ("epistemic_stability.html", "Epistemic Stability"),
            ("multi_video_analysis.html", "Multi-Video Analysis"),
            ("style_fingerprint.html", "Style Fingerprints"),
            ("creator_evolution.html", "Creator Evolution"),
            ("structural_pattern_mining.html", "Structural Pattern Mining"),
            ("semantic_equivalence_scaffolding.html", "Semantic Equivalence Scaffolding"),
        ]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(title)}</title>
  <link rel="stylesheet" href="../static_assets/report.css">
</head>
<body>
  <aside class="sidebar">
    <div class="brand">Video Insight Bundler</div>
    <nav>{nav}</nav>
  </aside>
  <main class="main">
    {body}
  </main>
  <script src="../static_assets/report.js"></script>
</body>
</html>
"""


def _metric(label: str, value) -> str:
    return f'<div class="metric"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _graph(src: str, title: str, note: str = "") -> str:
    spec = CORE_GRAPHS.get(title)
    if spec:
        detail = spec["detail"]
        note_html = f'<p class="muted">{_e(note)}</p>' if note else ""
        return (
            '<article class="graph-card graph-clickthrough-card">'
            f'<a class="graph-card-image-link" href="{_e(detail)}"><img src="../graphs/{_e(src)}" alt="{_e(title)} graph"></a>'
            f'<h3><a href="{_e(detail)}">{_e(title)}</a></h3>'
            f'<p class="graph-card-subtitle">{_e(spec["measures"])}</p>'
            f'<p class="graph-card-interpretation">{_e(spec["current"])}</p>'
            f'<a class="button more-link" href="{_e(detail)}">Explain this graph</a>'
            f'{note_html}'
            '</article>'
        )
    href = EXTENDED_GRAPH_DETAIL_LINKS.get(title, f"../graphs/{src}")
    action = "Open detail" if title in EXTENDED_GRAPH_DETAIL_LINKS else "Open graph image"
    note_html = f'<p class="muted">{_e(note)}</p>' if note else ""
    return (
        '<article class="graph-card graph-clickthrough-card">'
        f'<a class="graph-card-image-link" href="{_e(href)}"><img src="../graphs/{_e(src)}" alt="{_e(title)} graph"></a>'
        f'<h3><a href="{_e(href)}">{_e(title)}</a></h3>'
        f'<p class="graph-card-subtitle">{_e(note or "Dashboard graph evidence.")}</p>'
        '<p class="graph-card-interpretation">Open the linked detail page or graph image for the supporting evidence view.</p>'
        f'<a class="button more-link" href="{_e(href)}">{_e(action)}</a>'
        f'{note_html}'
        '</article>'
    )


def _link_list(items: list[tuple[str, str]]) -> str:
    return "<div class='link-grid'>" + "".join(f"<a href='{_e(href)}'>{_e(label)}</a>" for label, href in items) + "</div>"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _segment_rows(segments: list[dict], emotional: list[dict]) -> str:
    tone = {row.get("segment_id"): row for row in emotional}
    rows = []
    for index, segment in enumerate(segments):
        arc = tone.get(segment.get("segment_id"), {})
        rows.append(
            "<tr>"
            f"<td>{index + 1}</td><td>{_e(segment.get('start_sec'))}-{_e(segment.get('end_sec'))}s</td>"
            f"<td>{_e(segment.get('duration_sec'))}</td><td>{_e(segment.get('speech_rate_wpm'))}</td>"
            f"<td><span class='tone'>{_e(arc.get('dominant_tone', 'neutral'))}</span></td>"
            f"<td>{_e(', '.join(segment.get('topic_markers') or []))}</td>"
            f"<td>{_e(segment.get('summary') or '[no transcript]')}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='7'>No segments available.</td></tr>"


def _profile_cards(profile: dict) -> str:
    cards = []
    for row in profile.get("top_categories", [])[:8]:
        evidence = "; ".join(row.get("evidence") or ["limited evidence"])
        cards.append(
            f"<article class='score-card'><div><strong>{_e(row.get('label'))}</strong><span>{_e(row.get('description'))}</span></div>"
            f"<meter min='0' max='1' value='{_e(row.get('weight', 0))}'></meter>"
            f"<p>{_e(evidence)}</p></article>"
        )
    return "\n".join(cards) or "<p>No profile scores available.</p>"


def write_visualizations(bundle, report_data: dict, graph_status: dict) -> dict:
    vis_dir = bundle.output_dir / "visualizations"
    vis_dir.mkdir(exist_ok=True)
    _copy_assets(bundle.output_dir)
    segments = bundle.scene_segments.get("segments") or []
    emotional = bundle.emotional_arc.get("segments") or []
    transcript_segments = bundle.transcript.get("segments") or []
    acoustic = getattr(bundle, "acoustic_features", None) or {}
    topic = getattr(bundle, "topic_analysis", None) or {}
    rhetoric = getattr(bundle, "rhetorical_analysis", None) or {}
    recommendations_json = getattr(bundle, "recommendations_json", None) or {}
    consensus_outputs = getattr(bundle, "consensus_outputs", None) or {}
    evidence_consensus = consensus_outputs.get("evidence_consensus") or {}
    transition_confidence = consensus_outputs.get("transition_confidence") or {}
    continuity_analysis = consensus_outputs.get("continuity_analysis") or {}
    modality_agreement = consensus_outputs.get("modality_agreement") or {}
    modality_disagreement = consensus_outputs.get("modality_disagreement") or {}
    evidence_scores = consensus_outputs.get("evidence_score_summary") or {}
    false_positive = consensus_outputs.get("false_positive_boundaries") or {}
    topic_continuity = getattr(bundle, "topic_continuity", None) or {}
    rhetorical_coherence = getattr(bundle, "rhetorical_coherence", None) or {}
    boundary_diagnostics = getattr(bundle, "boundary_diagnostics", None) or {}
    discourse_state = getattr(bundle, "discourse_state", None) or {}
    argument_graph = getattr(bundle, "argument_graph", None) or {}
    narrative_memory = getattr(bundle, "narrative_memory", None) or {}
    callback_resolution = getattr(bundle, "callback_resolution", None) or {}
    editorial_ambiguity = getattr(bundle, "editorial_ambiguity", None) or {}
    discourse_summary = getattr(bundle, "discourse_summary", None) or {}
    visual_structure = getattr(bundle, "visual_structure", None) or {}
    shot_boundaries = getattr(bundle, "shot_boundaries", None) or {}
    visual_continuity = getattr(bundle, "visual_continuity", None) or {}
    composition_features = getattr(bundle, "composition_features", None) or {}
    visual_boundary_alignment = getattr(bundle, "visual_boundary_alignment", None) or {}
    artifact_integrity = _read_json(bundle.output_dir / "integrity" / "artifact_integrity.json")
    graph_consistency = _read_json(bundle.output_dir / "integrity" / "graph_consistency.json")
    reference_validation = _read_json(bundle.output_dir / "integrity" / "reference_validation.json")
    lineage_validation = _read_json(bundle.output_dir / "integrity" / "lineage_validation.json")
    dashboard_coverage = _read_json(bundle.output_dir / "integrity" / "dashboard_coverage.json")
    longitudinal_summary = _read_json(bundle.output_dir / "longitudinal" / "longitudinal_summary.json")
    sequence_summary = _read_json(bundle.output_dir / "sequence" / "sequence_summary.json")
    comparative_summary = _read_json(bundle.output_dir / "comparative" / "comparative_summary.json")
    quality = report_data.get("quality_scores", {})
    statuses = {
        "media_probe": bundle.media_metadata.get("probe_status"),
        "transcription": bundle.transcript.get("transcription_status"),
        "segmentation": bundle.scene_segments.get("segmentation_status"),
        "emotional_arc": bundle.emotional_arc.get("analysis_status"),
        "acoustic_analysis": acoustic.get("analysis_status"),
        "topic_analysis": topic.get("analysis_status"),
        "rhetorical_analysis": rhetoric.get("analysis_status"),
        "visual_graphs": graph_status.get("status"),
        "evidence_consensus": evidence_consensus.get("analysis_status"),
        "visual_structure": visual_structure.get("analysis_status"),
        "sequence_intelligence": sequence_summary.get("analysis_status"),
        "comparative_intelligence": comparative_summary.get("analysis_status"),
    }
    interactive_status = _write_interactive_outputs(bundle)
    top_recommendations = recommendations_json.get("recommendations", [])[:5]
    detail_links = [
        ("Transcript Explorer", "transcript_explorer.html"),
        ("Emotional Arc", "emotional_arc.html"),
        ("Pacing", "pacing_analysis.html"),
        ("Acoustic Analysis", "acoustic_analysis.html"),
        ("Topic Analysis", "topic_analysis.html"),
        ("Rhetorical Deep Dive", "rhetorical_deep_dive.html"),
        ("Segment Quality", "segment_quality.html"),
        ("Frame Contact Sheet", "frame_contact_sheet.html"),
        ("Recommendations", "recommendations_report.html"),
        ("Revision Graph", "revision_graph.html"),
        ("Branch Comparison", "revision_comparison.html"),
        ("Release Readiness", "release_readiness.html"),
        ("Mutation Safety", "mutation_safety.html"),
        ("Editorial Evolution", "editorial_evolution.html"),
        ("Evidence Consensus", "evidence_consensus.html"),
        ("Continuity", "continuity_analysis.html"),
        ("Segmentation Confidence", "segmentation_confidence.html"),
        ("Modality Alignment", "modality_alignment.html"),
        ("Topic Continuity", "topic_continuity.html"),
        ("Rhetorical Coherence", "rhetorical_coherence.html"),
        ("Boundary Diagnostics", "boundary_diagnostics.html"),
        ("Discourse State", "discourse_state.html"),
        ("Argument Graph", "argument_graph.html"),
        ("Narrative Memory", "narrative_memory.html"),
        ("Callback Resolution", "callback_resolution.html"),
        ("Editorial Ambiguity", "editorial_ambiguity.html"),
        ("Visual Structure", "visual_structure.html"),
        ("Shot Boundaries", "shot_boundaries.html"),
        ("Visual Continuity", "visual_continuity.html"),
        ("Composition Features", "composition_features.html"),
        ("Visual Boundary Alignment", "visual_boundary_alignment.html"),
        ("Artifact Integrity", "artifact_integrity.html"),
        ("Graph Consistency", "graph_consistency.html"),
        ("Reference Validation", "reference_validation.html"),
        ("Lineage Validation", "lineage_validation.html"),
        ("Migration Registry", "migration_registry.html"),
        ("Semantic Readiness", "semantic_readiness.html"),
        ("Run History", "run_history.html"),
        ("Artifact Drift", "artifact_drift.html"),
        ("Metric Drift", "metric_drift.html"),
        ("Readiness Drift", "readiness_drift.html"),
        ("Longitudinal Analysis", "longitudinal_analysis.html"),
        ("Trend Analysis", "trend_analysis.html"),
        ("Confidence Volatility", "confidence_volatility.html"),
        ("Recommendation Evolution", "recommendation_evolution.html"),
        ("Anomaly Clusters", "anomaly_clusters.html"),
        ("Persistent Patterns", "persistent_patterns.html"),
        ("Semantic Evolution", "semantic_evolution.html"),
        ("Sequence Intelligence", "sequence_structure.html"),
        ("Scene Hierarchy", "scene_hierarchy.html"),
        ("Temporal Rhythm", "temporal_rhythm.html"),
        ("Narrative Phase Structure", "narrative_phase_model.html"),
        ("Editorial Pressure", "editorial_pressure.html"),
        ("Recommendation Dependencies", "recommendation_dependencies.html"),
        ("Revision Propagation", "revision_propagation.html"),
        ("Counterfactual Simulation", "counterfactual_simulation.html"),
        ("Revision Forecasting", "revision_forecasting.html"),
        ("Epistemic Stability", "epistemic_stability.html"),
        ("Multi-Video Analysis", "multi_video_analysis.html"),
        ("Style Fingerprints", "style_fingerprint.html"),
        ("Rhetorical Fingerprint", "rhetorical_fingerprint.html"),
        ("Pacing Fingerprint", "pacing_fingerprint.html"),
        ("Discourse Fingerprint", "discourse_fingerprint.html"),
        ("Creator Evolution", "creator_evolution.html"),
        ("Structural Pattern Mining", "structural_pattern_mining.html"),
        ("Comparative Recommendations", "comparative_recommendations.html"),
        ("Semantic Equivalence Scaffolding", "semantic_equivalence_scaffolding.html"),
    ]
    report_links = [
        ("Manifest", "../manifest.json"),
        ("Analysis Index JSON", "../analysis_index.json"),
        ("Analysis Index MD", "../analysis_index.md"),
        ("Recommendations JSON", "../recommendations.json"),
        ("LLM Bundle MD", "../llm_context_bundle.md"),
        ("LLM Bundle JSON", "../llm_context_bundle.json"),
        ("Quality JSON", "../reports/quality_report.json"),
        ("Acoustic Stats", "../reports/acoustic_statistics.json"),
        ("Topic Stats", "../reports/topic_statistics.json"),
        ("Rhetorical Deep Dive JSON", "../reports/rhetorical_deep_dive.json"),
        ("Revision Graph JSON", "../revision_graph/revision_graph.json"),
        ("Release Readiness JSON", "../revision_graph/release_readiness_report.json"),
        ("Branch Comparison JSON", "../revision_graph/branch_comparison_report.json"),
        ("Mutation Safety JSON", "../revision_graph/mutation_safety_contract.json"),
        ("Evidence Consensus JSON", "../consensus/evidence_consensus.json"),
        ("Transition Confidence JSON", "../consensus/transition_confidence.json"),
        ("Continuity JSON", "../consensus/continuity_analysis.json"),
        ("Topic Continuity JSON", "../continuity/topic_continuity.json"),
        ("Rhetorical Coherence JSON", "../continuity/rhetorical_coherence.json"),
        ("Boundary Diagnostics JSON", "../continuity/boundary_diagnostics.json"),
        ("Discourse State JSON", "../discourse/discourse_state.json"),
        ("Argument Graph JSON", "../discourse/argument_graph.json"),
        ("Narrative Memory JSON", "../discourse/narrative_memory.json"),
        ("Callback Resolution JSON", "../discourse/callback_resolution.json"),
        ("Editorial Ambiguity JSON", "../discourse/editorial_ambiguity.json"),
        ("Discourse Summary JSON", "../discourse/discourse_summary.json"),
        ("Visual Structure JSON", "../visual_structure/visual_structure.json"),
        ("Shot Boundaries JSON", "../visual_structure/shot_boundaries.json"),
        ("Visual Continuity JSON", "../visual_structure/visual_continuity.json"),
        ("Composition Features JSON", "../visual_structure/composition_features.json"),
        ("Visual Boundary Alignment JSON", "../visual_structure/visual_boundary_alignment.json"),
        ("Evidence Score Summary", "../consensus/evidence_score_summary.json"),
        ("Discourse Schema Validation", "../verification_evidence/discourse_schema_validation.json"),
        ("Visual Structure Validation", "../verification_evidence/visual_structure_validation.json"),
        ("Revision Schema Validation", "../verification_evidence/revision_schema_validation.json"),
        ("Artifact Integrity JSON", "../integrity/artifact_integrity.json"),
        ("Graph Consistency JSON", "../integrity/graph_consistency.json"),
        ("Reference Validation JSON", "../integrity/reference_validation.json"),
        ("Lineage Validation JSON", "../integrity/lineage_validation.json"),
        ("Dashboard Coverage JSON", "../integrity/dashboard_coverage.json"),
        ("Migration Registry JSON", "../integrity/migration_registry.json"),
        ("Semantic Readiness JSON", "../integrity/semantic_readiness.json"),
        ("Run History JSON", "../history/run_history.json"),
        ("Run Comparison JSON", "../history/run_comparison.json"),
        ("Artifact Drift JSON", "../history/artifact_drift_report.json"),
        ("Metric Drift JSON", "../history/metric_drift_report.json"),
        ("Readiness Drift JSON", "../history/readiness_drift_report.json"),
        ("Longitudinal Summary JSON", "../longitudinal/longitudinal_summary.json"),
        ("Longitudinal Analysis JSON", "../longitudinal/longitudinal_analysis.json"),
        ("Trend Analysis JSON", "../longitudinal/trend_analysis.json"),
        ("Confidence Volatility JSON", "../longitudinal/confidence_volatility.json"),
        ("Recommendation Evolution JSON", "../longitudinal/recommendation_evolution.json"),
        ("Anomaly Clusters JSON", "../longitudinal/anomaly_clusters.json"),
        ("Persistent Patterns JSON", "../longitudinal/persistent_patterns.json"),
        ("Semantic Evolution JSON", "../longitudinal/semantic_evolution.json"),
        ("Longitudinal Validation JSON", "../verification_evidence/longitudinal_validation.json"),
        ("Sequence Summary JSON", "../sequence/sequence_summary.json"),
        ("Sequence Structure JSON", "../sequence/sequence_structure.json"),
        ("Temporal Rhythm JSON", "../sequence/temporal_rhythm.json"),
        ("Narrative Phase JSON", "../sequence/narrative_phase_model.json"),
        ("Editorial Pressure JSON", "../sequence/editorial_pressure.json"),
        ("Recommendation Dependencies JSON", "../sequence/recommendation_dependencies.json"),
        ("Revision Propagation JSON", "../sequence/revision_propagation.json"),
        ("Counterfactual Simulation JSON", "../sequence/counterfactual_simulation.json"),
        ("Epistemic Stability JSON", "../sequence/epistemic_stability.json"),
        ("Temporal Structure Validation", "../verification_evidence/temporal_structure_validation.json"),
        ("Revision Simulation Validation", "../verification_evidence/revision_simulation_validation.json"),
        ("Comparative Summary JSON", "../comparative/comparative_summary.json"),
        ("Multi-Video Analysis JSON", "../comparative/multi_video_analysis.json"),
        ("Style Fingerprint JSON", "../comparative/style_fingerprint.json"),
        ("Creator Evolution JSON", "../comparative/creator_evolution.json"),
        ("Structural Pattern Mining JSON", "../comparative/structural_pattern_mining.json"),
        ("Semantic Equivalence Scaffolding JSON", "../comparative/semantic_equivalence_scaffolding.json"),
        ("Comparative Validation JSON", "../verification_evidence/comparative_validation.json"),
    ]

    dashboard = _page("Analysis Dashboard", "dashboard.html", f"""
<header class="page-header"><p>Multimodal Analysis Workstation</p><h1>{_e(Path(bundle.source_video).stem)}</h1></header>
<section class="metrics">
  {_metric("Duration", bundle.media_metadata.get("duration_sec"))}
  {_metric("Resolution", f"{bundle.media_metadata.get('width')}x{bundle.media_metadata.get('height')}")}
  {_metric("Words", bundle.audio_features.get("word_count"))}
  {_metric("Overall WPM", bundle.audio_features.get("overall_words_per_minute"))}
  {_metric("Segments", len(segments))}
  {_metric("Warnings", len(bundle.warnings))}
  {_metric("Topic Drift", topic.get("topic_drift_score"))}
  {_metric("Topic Continuity", topic_continuity.get("topic_continuity_score"))}
  {_metric("Rhetorical Coherence", rhetorical_coherence.get("rhetorical_coherence_score"))}
  {_metric("Argument Complete", argument_graph.get("argument_completeness_score"))}
  {_metric("Narrative Persist", narrative_memory.get("thematic_persistence_score"))}
  {_metric("Callback Quality", callback_resolution.get("payoff_quality_score"))}
  {_metric("Ambiguity Adjusted", discourse_summary.get("ambiguity_adjusted_continuity"))}
  {_metric("Silence Ratio", acoustic.get("silence_ratio"))}
  {_metric("Consensus", (evidence_consensus.get("summary", {}).get("consensus_score_distribution") or {}).get("mean"))}
  {_metric("False Positive Ratio", false_positive.get("false_positive_boundary_ratio"))}
  {_metric("Visual Boundaries", visual_structure.get("shot_boundary_count"))}
  {_metric("Visual Continuity", visual_structure.get("visual_continuity_score"))}
  {_metric("Visual Alignment", visual_structure.get("visual_boundary_alignment_quality"))}
  {_metric("Artifact Integrity", artifact_integrity.get("integrity_score"))}
  {_metric("Graph Consistency", graph_consistency.get("graph_integrity_score"))}
  {_metric("Reference Integrity", reference_validation.get("reference_integrity_score"))}
  {_metric("Lineage Consistency", lineage_validation.get("lineage_consistency_score"))}
  {_metric("Dashboard Coverage", dashboard_coverage.get("dashboard_coverage_score"))}
  {_metric("Longitudinal Confidence", longitudinal_summary.get("longitudinal_confidence"))}
  {_metric("Volatility Score", longitudinal_summary.get("volatility_score"))}
  {_metric("Structural Coherence", sequence_summary.get("structural_coherence_score"))}
  {_metric("Peak Pressure", sequence_summary.get("peak_cumulative_pressure_score"))}
  {_metric("Epistemic Stability", sequence_summary.get("epistemic_stability_score"))}
  {_metric("Creator Evolution", comparative_summary.get("creator_evolution_classification"))}
  {_metric("Comparative Volatility", comparative_summary.get("comparative_volatility"))}
</section>
<section class="grid two">
  {_graph("emotional_arc.png", "Emotional Arc", "tone, valence, certainty, energy")}
  {_graph("pacing_curve.png", "Pacing Curve", "words per minute over time")}
  {_graph("acoustic_energy_curve.png", "Acoustic Energy", "local RMS energy evidence")}
  {_graph("topic_timeline.png", "Topic Timeline", "deterministic transcript terms")}
  {_graph("keyword_clusters.png", "Keyword Clusters", "deterministic keyword grouping")}
  {_graph("rhetorical_mode_timeline.png", "Rhetorical Modes", "marker-based modes")}
  {_graph("persona_radar.png", "Persona / Style Radar", "weighted category evidence")}
  {_graph("transition_confidence_curve.png", "Transition Confidence", "fused boundary evidence")}
  {_graph("modality_agreement_heatmap.png", "Modality Agreement", "pairwise evidence alignment")}
  {_graph("discourse_flow_graph.png", "Discourse Flow", "continuation and pressure")}
  {_graph("argument_chain_graph.png", "Argument Chains", "deterministic claim/support graph")}
  {_graph("callback_resolution_map.png", "Callback Map", "setup/payoff latency and quality")}
  {_graph("narrative_memory_timeline.png", "Narrative Memory", "theme recurrence")}
  {_graph("discourse_pressure_curve.png", "Discourse Pressure", "unresolved state over time")}
  {_graph("ambiguity_distribution.png", "Ambiguity Distribution", "continuity reinterpretation classes")}
  {_graph("shot_boundary_curve.png", "Shot Boundary Curve", "local visual-change evidence")}
  {_graph("visual_continuity_timeline.png", "Visual Continuity", "similarity and change over time")}
  {_graph("visual_boundary_alignment.png", "Visual Boundary Alignment", "visual vs transcript/discourse support")}
  {_graph("artifact_dependency_graph.png", "Artifact Dependency Graph", "cross-artifact integrity")}
  {_graph("graph_consistency_matrix.png", "Graph Consistency Matrix", "graph validation summary")}
  {_graph("orphan_reference_map.png", "Orphan Reference Map", "invalid and orphan references")}
  {_graph("lineage_flow_graph.png", "Lineage Flow", "revision lineage validation")}
  {_graph("dashboard_coverage_heatmap.png", "Dashboard Coverage", "static link coverage")}
  {_graph("semantic_readiness_map.png", "Semantic Readiness", "future interface boundaries")}
  {_graph("readiness_drift_timeline.png", "Readiness Drift", "historical readiness comparison")}
  {_graph("metric_drift_heatmap.png", "Metric Drift", "meaningful metric deltas")}
  {_graph("artifact_drift_matrix.png", "Artifact Drift", "hash changes and missing artifacts")}
  {_graph("dependency_drift_timeline.png", "Dependency Drift", "local dependency version changes")}
  {_graph("readiness_trend.png", "Readiness Trend", "longitudinal readiness evolution")}
  {_graph("continuity_trend.png", "Continuity Trend", "longitudinal continuity evolution")}
  {_graph("contradiction_trend.png", "Contradiction Trend", "longitudinal contradiction evolution")}
  {_graph("confidence_volatility_curve.png", "Confidence Volatility", "historical metric volatility")}
  {_graph("recommendation_evolution_map.png", "Recommendation Evolution", "recommendation count and confidence")}
  {_graph("persistent_weakness_heatmap.png", "Persistent Weaknesses", "chronic issue pressure")}
  {_graph("anomaly_cluster_graph.png", "Anomaly Clusters", "longitudinal anomaly groups")}
  {_graph("discourse_evolution_timeline.png", "Discourse Evolution", "argument completeness over runs")}
  {_graph("semantic_readiness_timeline.png", "Semantic Readiness Timeline", "longitudinal semantic scaffold")}
  {_graph("pacing_wave_timeline.png", "Pacing Wave Timeline", "sequence-level intensity waves")}
  {_graph("temporal_rhythm.png", "Temporal Rhythm", "density rhythm")}
  {_graph("narrative_phase_map.png", "Narrative Phase Map", "rule-based phase structure")}
  {_graph("editorial_pressure_curve.png", "Editorial Pressure", "pressure accumulation")}
  {_graph("contradiction_pressure_curve.png", "Contradiction Pressure", "contradiction pressure accumulation")}
  {_graph("recommendation_dependency_graph.png", "Recommendation Dependencies", "interaction graph")}
  {_graph("revision_propagation_graph.png", "Revision Propagation", "proposal-only estimates")}
  {_graph("structural_transition_map.png", "Structural Transitions", "sequence pivot map")}
  {_graph("epistemic_stability_curve.png", "Epistemic Stability", "evidence convergence")}
  {_graph("creator_evolution_timeline.png", "Creator Evolution", "comparative trajectory")}
  {_graph("creator_stability_curve.png", "Creator Stability", "creator-level stability")}
  {_graph("recurring_pattern_heatmap.png", "Recurring Patterns", "structural motifs")}
  {_graph("semantic_equivalence_readiness_map.png", "Semantic Equivalence Scaffolding", "future hook readiness")}
</section>
<section class="panel"><h2>Quality Scores</h2><div class="metrics compact">{''.join(_metric(k.replace('_', ' ').title(), v) for k, v in quality.items())}</div></section>
<section class="panel"><h2>Consensus Summary</h2>{_consensus_summary(consensus_outputs)}</section>
<section class="panel"><h2>Topic Continuity</h2><div class="metrics compact">{_metric("Score", topic_continuity.get("topic_continuity_score"))}{_metric("Unsupported Shifts", len(topic_continuity.get("unsupported_topic_shifts") or []))}{_metric("Re-entries", len(topic_continuity.get("topic_reentry_points") or []))}</div></section>
<section class="panel"><h2>Rhetorical Coherence</h2><div class="metrics compact">{_metric("Score", rhetorical_coherence.get("rhetorical_coherence_score"))}{_metric("Unresolved Questions", len(rhetorical_coherence.get("unresolved_questions") or []))}{_metric("Claims Without Examples", len(rhetorical_coherence.get("claims_without_examples") or []))}</div></section>
<section class="panel"><h2>Boundary Diagnostics</h2><div class="metrics compact">{_metric("Needs Review", (boundary_diagnostics.get("summary") or {}).get("likely_review_boundary_count"))}{_metric("Contradictions", (boundary_diagnostics.get("summary") or {}).get("total_contradictions"))}{_metric("Mean Support", (boundary_diagnostics.get("summary") or {}).get("mean_consensus_support"))}</div></section>
<section class="panel"><h2>Visual Structure</h2><div class="metrics compact">{_metric("Shot Boundaries", visual_structure.get("shot_boundary_count"))}{_metric("Continuity Score", visual_structure.get("visual_continuity_score"))}{_metric("Evidence Completeness", visual_structure.get("visual_evidence_completeness"))}{_metric("Contradiction Pressure", visual_structure.get("visual_contradiction_pressure"))}</div></section>
<section class="panel"><h2>Continuity Decomposition</h2><div class="metrics compact">{''.join(_metric(k.replace('_', ' ').title(), v) for k, v in (discourse_summary.get('decomposed_scores') or {}).items())}</div></section>
<section class="panel"><h2>Subsystem Statuses</h2><div class="status-grid">{''.join(f"<div><span>{_e(k)}</span><strong>{_e(v)}</strong></div>" for k, v in statuses.items())}</div></section>
<section class="panel"><h2>Top Insights</h2>{_top_insights(acoustic, topic, rhetoric, quality)}</section>
<section class="panel"><h2>Top Recommendations</h2>{_recommendation_cards(top_recommendations)}</section>
<section class="panel"><h2>Revision Intelligence</h2>{_revision_intelligence(bundle.output_dir)}</section>
<section class="panel"><h2>Graph Explanation Shortcuts</h2><p><a href="graph_ux/graph_detail_index.html">Graph detail index</a></p></section>
<section class="panel"><h2>Detailed Pages</h2>{grouped_detail_links_html(detail_links)}</section>
<section class="panel"><h2>Reports and Bundles</h2>{_link_list(report_links)}</section>
<section class="panel"><h2>Interactive Exports</h2>{_interactive_links(interactive_status)}</section>
<section class="panel"><h2>Segment Explorer</h2><table><thead><tr><th>#</th><th>Time</th><th>Duration</th><th>WPM</th><th>Tone</th><th>Markers</th><th>Summary</th></tr></thead><tbody>{_segment_rows(segments, emotional)}</tbody></table></section>
<section class="panel"><h2>Warnings</h2>{_warnings(bundle.warnings)}</section>
""")
    (vis_dir / "dashboard.html").write_text(dashboard, encoding="utf-8")
    ensure_core_detail_pages(bundle.output_dir)
    ensure_graph_detail_index(bundle.output_dir)

    transcript_payload = []
    tone_by_time = [(row.get("start_sec"), row.get("end_sec"), row.get("dominant_tone"), row.get("intensity")) for row in emotional]
    for segment in transcript_segments:
        transcript_payload.append({
            "start": segment.get("start"),
            "end": segment.get("end"),
            "text": segment.get("text", ""),
            "markers": _matching_markers(segment.get("text", "")),
            "tone": _tone_for(segment.get("start"), tone_by_time),
            "wpm": _wpm_for(segment),
        })
    transcript_page = _page("Transcript Explorer", "transcript_explorer.html", f"""
<header class="page-header"><p>Evidence Browser</p><h1>Transcript Explorer</h1></header>
<section class="toolbar"><input id="transcriptSearch" type="search" placeholder="Search transcript"><select id="toneFilter"><option value="">All tones</option><option>analytical</option><option>instructional</option><option>motivational</option><option>critical</option><option>reflective</option><option>neutral</option></select></section>
<section id="transcriptList" class="transcript-list"></section>
<script id="transcriptData" type="application/json">{_json(transcript_payload)}</script>
""")
    (vis_dir / "transcript_explorer.html").write_text(transcript_page, encoding="utf-8")

    simple_pages = {
        "emotional_arc.html": ("Emotional Arc", [_graph("emotional_arc.png", "Emotional Arc"), _arc_table(emotional)]),
        "pacing_analysis.html": ("Pacing Analysis", [_graph("pacing_curve.png", "Pacing Curve"), _graph("pause_distribution.png", "Pause Distribution"), _json_block(report_data.get("pacing_statistics", {}))]),
        "persona_analysis.html": ("Persona / Style", [_graph("persona_radar.png", "Persona Radar"), "<section class='panel'><h2>Persona Evidence</h2>" + _profile_cards(bundle.persona_profile) + "</section>", "<section class='panel'><h2>Teaching Style Evidence</h2>" + _profile_cards(bundle.teaching_profile) + "</section>"]),
        "rhetorical_flow.html": ("Rhetorical Flow", [_graph("rhetorical_heatmap.png", "Rhetorical Heatmap"), _graph("rhetorical_markers_network.png", "Marker Network"), _json_block(report_data.get("rhetorical_statistics", {}))]),
        "segment_timeline.html": ("Segment Timeline", [_graph("segment_timeline.png", "Segment Timeline"), f"<section class='panel'><table><thead><tr><th>#</th><th>Time</th><th>Duration</th><th>WPM</th><th>Tone</th><th>Markers</th><th>Summary</th></tr></thead><tbody>{_segment_rows(segments, emotional)}</tbody></table></section>"]),
        "transcript_density.html": ("Transcript Density", [_graph("transcript_density.png", "Transcript Density"), _graph("speaking_rate_distribution.png", "Speaking Rate Distribution"), _graph("wordcloud.png", "Word Cloud"), _keywords(report_data)]),
        "recommendations_report.html": ("Recommendations", [_recommendation_cards(recommendations_json.get("recommendations", [])), f"<section class='panel prose'>{_markdownish(bundle.recommendations_md)}</section>", f"<section class='panel prose'>{_markdownish((bundle.output_dir / 'reports' / 'quality_report.md').read_text(encoding='utf-8'))}</section>"]),
        "acoustic_analysis.html": ("Acoustic Analysis", [_graph("acoustic_energy_curve.png", "Acoustic Energy Curve"), _graph("segment_energy_bars.png", "Segment Energy Bars"), _graph("silence_ratio.png", "Silence Ratio"), _graph("acoustic_variability.png", "Acoustic Variability"), _json_block(report_data.get("acoustic_statistics", {}))]),
        "topic_analysis.html": ("Topic Analysis", [_graph("topic_timeline.png", "Topic Timeline"), _graph("topic_shift_heatmap.png", "Topic Shift Heatmap"), _graph("keyword_importance.png", "Keyword Importance"), _graph("concept_repetition.png", "Concept Repetition"), _json_block(report_data.get("topic_statistics", {}))]),
        "rhetorical_deep_dive.html": ("Rhetorical Deep Dive", [_graph("rhetorical_mode_timeline.png", "Rhetorical Mode Timeline"), _graph("question_density.png", "Question Density"), _graph("claim_example_balance.png", "Claim / Example Balance"), _graph("abstract_vs_concrete.png", "Abstract vs Concrete"), _graph("audience_address_curve.png", "Audience Address Curve"), _json_block(report_data.get("rhetorical_deep_dive", {}))]),
        "segment_quality.html": ("Segment Quality", [_graph("segment_boundary_confidence.png", "Segment Boundary Confidence"), _json_block(report_data.get("segment_boundary_report", {})), f"<section class='panel'><table><thead><tr><th>#</th><th>Time</th><th>Boundary</th><th>Confidence</th><th>Coherence</th><th>Summary</th></tr></thead><tbody>{_segment_quality_rows(segments)}</tbody></table></section>"]),
        "frame_contact_sheet.html": ("Frame Contact Sheet", [_graph("frame_contact_sheet.png", "Frame Contact Sheet"), f"<section class='panel'><table><thead><tr><th>Frame</th><th>Time</th><th>Segment</th><th>Status</th><th>Reason</th><th>Snippet</th></tr></thead><tbody>{_frame_rows(bundle.visual_index.get('samples') or [], segments, transcript_segments)}</tbody></table></section>"]),
        "evidence_consensus.html": ("Evidence Consensus", [_graph("evidence_strength_distribution.png", "Evidence Strength Distribution"), _graph("modality_agreement_heatmap.png", "Modality Agreement Heatmap"), _graph("modality_disagreement_heatmap.png", "Modality Disagreement Heatmap"), _consensus_table(evidence_consensus), _json_block(evidence_consensus.get("summary", {}))]),
        "continuity_analysis.html": ("Continuity Analysis", [_graph("continuity_alignment.png", "Continuity Alignment"), _continuity_table(continuity_analysis), _json_block(continuity_analysis.get("summary", {}))]),
        "segmentation_confidence.html": ("Segmentation Confidence", [_graph("transition_confidence_curve.png", "Transition Confidence Curve"), _graph("false_positive_boundaries.png", "False-Positive Boundaries"), _graph("segmentation_confidence.png", "Segmentation Confidence"), _transition_table(transition_confidence), _json_block(false_positive)]),
        "modality_alignment.html": ("Modality Alignment", [_graph("modality_agreement_heatmap.png", "Agreement Heatmap"), _graph("modality_disagreement_heatmap.png", "Disagreement Heatmap"), _modality_table(modality_agreement, modality_disagreement)]),
        "topic_continuity.html": ("Topic Continuity", [_graph("topic_continuity_curve.png", "Topic Continuity Curve"), _graph("topic_bridge_map.png", "Topic Bridge Map"), _json_block(topic_continuity)]),
        "rhetorical_coherence.html": ("Rhetorical Coherence", [_graph("rhetorical_coherence_timeline.png", "Rhetorical Coherence Timeline"), _graph("claim_evidence_balance.png", "Claim / Evidence Balance"), _json_block(rhetorical_coherence)]),
        "boundary_diagnostics.html": ("Boundary Diagnostics", [_graph("boundary_diagnostic_matrix.png", "Boundary Diagnostic Matrix"), _boundary_diagnostics_table(boundary_diagnostics), _json_block(boundary_diagnostics.get("summary", {}))]),
        "discourse_state.html": ("Discourse State", [_graph("discourse_flow_graph.png", "Discourse Flow Graph"), _graph("discourse_pressure_curve.png", "Discourse Pressure Curve"), _discourse_state_table(discourse_state), _json_block(discourse_summary)]),
        "argument_graph.html": ("Argument Graph", [_graph("argument_chain_graph.png", "Argument Chain Graph"), _graph("unresolved_argument_map.png", "Unresolved Argument Map"), _argument_graph_table(argument_graph), _json_block(argument_graph.get("contradiction_clusters", []))]),
        "narrative_memory.html": ("Narrative Memory", [_graph("narrative_memory_timeline.png", "Narrative Memory Timeline"), _narrative_memory_table(narrative_memory), _json_block(narrative_memory)]),
        "callback_resolution.html": ("Callback Resolution", [_graph("callback_resolution_map.png", "Callback Resolution Map"), _callback_resolution_table(callback_resolution), _json_block(callback_resolution)]),
        "editorial_ambiguity.html": ("Editorial Ambiguity", [_graph("ambiguity_distribution.png", "Ambiguity Distribution"), _editorial_ambiguity_table(editorial_ambiguity), _json_block(editorial_ambiguity)]),
        "visual_structure.html": ("Visual Structure", [_graph("shot_boundary_curve.png", "Shot Boundary Curve"), _graph("visual_change_intensity.png", "Visual Change Intensity"), _graph("visual_boundary_alignment.png", "Visual Boundary Alignment"), _json_block(visual_structure)]),
        "shot_boundaries.html": ("Shot Boundaries", [_graph("shot_boundary_curve.png", "Shot Boundary Curve"), _graph("frame_difference_heatmap.png", "Frame Difference Heatmap"), _graph("shot_contact_sheet.png", "Shot Contact Sheet"), _shot_boundary_table(shot_boundaries), _json_block(shot_boundaries.get("boundary_confidence", {}))]),
        "visual_continuity.html": ("Visual Continuity", [_graph("visual_continuity_timeline.png", "Visual Continuity Timeline"), _graph("visual_change_intensity.png", "Visual Change Intensity"), _visual_continuity_table(visual_continuity), _json_block(visual_continuity.get("summary", {}))]),
        "composition_features.html": ("Composition Features", [_graph("composition_complexity_curve.png", "Composition Complexity Curve"), _composition_table(composition_features), _json_block(composition_features.get("summary", {}))]),
        "visual_boundary_alignment.html": ("Visual Boundary Alignment", [_graph("visual_boundary_alignment.png", "Visual Boundary Alignment"), _visual_alignment_table(visual_boundary_alignment), _json_block(visual_boundary_alignment.get("summary", {}))]),
    }
    for filename, (title, parts) in simple_pages.items():
        body = f"<header class='page-header'><p>Analysis View</p><h1>{_e(title)}</h1></header>" + "\n".join(parts)
        (vis_dir / filename).write_text(_page(title, filename, body), encoding="utf-8")
    enrichment = enrich_dashboard_pages(
        bundle.output_dir,
        {
            "recommendations": recommendations_json.get("recommendations", []),
            "statuses": statuses,
            "quality": quality,
        },
    )
    interpretation = run_dashboard_interpretation(bundle.output_dir, inject=True)
    completeness = run_dashboard_data_completeness(bundle.output_dir)
    placeholder_audit = run_placeholder_text_audit(bundle.output_dir)
    return {"status": "complete", "visualizations_dir": "visualizations/", "files": PAGE_NAMES, "interactive": interactive_status}


def _warnings(warnings: list[dict]) -> str:
    if not warnings:
        return "<p>No structured warnings emitted.</p>"
    return "<ul>" + "".join(f"<li><strong>{_e(item.get('code'))}</strong>: {_e(item.get('message'))}</li>" for item in warnings) + "</ul>"


def _top_insights(acoustic: dict, topic: dict, rhetoric: dict, quality: dict) -> str:
    items = [
        f"Topic drift score: {topic.get('topic_drift_score')}",
        f"Likely topic shifts: {len(topic.get('likely_topic_shifts') or [])}",
        f"Silence ratio: {acoustic.get('silence_ratio')}",
        f"Energy trend: {(acoustic.get('loudness_energy_trend') or {}).get('direction')}",
        f"Rhetorical balance score: {rhetoric.get('rhetorical_balance_score')}",
        f"Recommendation confidence: {quality.get('recommendation_confidence')}",
    ]
    return "<ul>" + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul>"


def _consensus_summary(consensus_outputs: dict) -> str:
    consensus = consensus_outputs.get("evidence_consensus") or {}
    transition = consensus_outputs.get("transition_confidence") or {}
    false_positive = consensus_outputs.get("false_positive_boundaries") or {}
    scores = consensus_outputs.get("evidence_score_summary") or {}
    summary = consensus.get("summary", {})
    items = [
        ("Mean Consensus", (summary.get("consensus_score_distribution") or {}).get("mean")),
        ("Strongest Agreements", len([row for row in consensus.get("consensus_items", []) if row.get("consensus_class") == "strong_agreement"])),
        ("Likely False Positives", false_positive.get("false_positive_boundary_count")),
        ("Transition Confidence", ((transition.get("summary", {}) or {}).get("confidence_distribution", {}) or {}).get("mean")),
        ("Evidence Strength", scores.get("overall_evidence_strength")),
    ]
    weak = ", ".join(row.get("modality") for row in scores.get("weakest_evidence", [])[:3]) or "none"
    return "<div class='metrics compact'>" + "".join(_metric(label, value) for label, value in items) + f"</div><p>Weakest evidence areas: {_e(weak)}</p>"


def _recommendation_cards(rows: list[dict]) -> str:
    if not rows:
        return "<p>No evidence-ranked recommendations available.</p>"
    cards = []
    for row in rows:
        cards.append(
            "<article class='score-card'>"
            f"<div><strong>{_e(row.get('issue_type'))}</strong><span>{_e(row.get('severity'))} | confidence {_e(row.get('confidence'))}</span></div>"
            f"<p>{_e(row.get('suggested_edit'))}</p>"
            f"<p><strong>Evidence:</strong> {_e('; '.join(row.get('evidence') or []))}</p>"
            f"<p><strong>Consensus:</strong> {_e((row.get('consensus_backing') or {}).get('consensus_score'))} | false-positive risk {_e((row.get('consensus_backing') or {}).get('false_positive_risk'))}</p>"
            f"<p><strong>Segments:</strong> {_e(', '.join(row.get('affected_segment_ids') or []))}</p>"
            "</article>"
        )
    return "\n".join(cards)


def _interactive_links(status: dict) -> str:
    files = status.get("files") or []
    if not files:
        reason = status.get("reason", "No interactive Plotly outputs were generated.")
        return f"<p>{_e(reason)}</p>"
    return _link_list([(Path(item).stem.replace("_", " ").title(), "../interactive/" + item) for item in files])


def _revision_intelligence(output_dir: Path) -> str:
    path = output_dir / "revision_graph" / "revision_recommendations.json"
    if not path.exists():
        return "<p>Revision graph artifacts were not generated for this run.</p>"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"<p>Revision graph summary unavailable: {_e(exc)}</p>"
    items = [
        ("Recommended Branch", data.get("recommended_branch")),
        ("Safest Action", data.get("safest_action")),
        ("Highest Score Action", data.get("highest_score_action")),
        ("Identity Preserving Action", data.get("best_identity_preserving_action")),
    ]
    links = _link_list(
        [
            ("Revision Graph", "revision_graph.html"),
            ("Branch Comparison", "revision_comparison.html"),
            ("Release Readiness", "release_readiness.html"),
            ("Mutation Safety", "mutation_safety.html"),
            ("Editorial Evolution", "editorial_evolution.html"),
            ("Evidence Consensus", "evidence_consensus.html"),
            ("Continuity", "continuity_analysis.html"),
            ("Segmentation Confidence", "segmentation_confidence.html"),
            ("Modality Alignment", "modality_alignment.html"),
        ]
    )
    return (
        "<div class='metrics compact'>"
        + "".join(_metric(label, value) for label, value in items)
        + "</div><p>Planning and simulation artifacts only; no edits are applied.</p>"
        + links
    )


def _segment_quality_rows(segments: list[dict]) -> str:
    rows = []
    for index, segment in enumerate(segments):
        boundary = segment.get("boundary") or {}
        rows.append(
            "<tr>"
            f"<td>{index + 1}</td>"
            f"<td>{_e(segment.get('start_sec'))}-{_e(segment.get('end_sec'))}s</td>"
            f"<td>{_e(boundary.get('transition_type'))}</td>"
            f"<td>{_e(boundary.get('confidence'))}</td>"
            f"<td>{_e(segment.get('segment_coherence_score'))}</td>"
            f"<td>{_e(segment.get('summary') or '[no transcript]')}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='6'>No segment quality rows available.</td></tr>"


def _consensus_table(data: dict) -> str:
    rows = []
    for item in data.get("consensus_items", [])[:80]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('transition_id'))}</td><td>{_e(item.get('consensus_score'))}</td><td>{_e(item.get('consensus_class'))}</td>"
            f"<td>{_e(', '.join(item.get('supporting_modalities') or []))}</td><td>{_e(', '.join(item.get('conflicting_modalities') or []))}</td>"
            f"<td>{_e(item.get('false_positive_probability'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='6'>No consensus rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Transition</th><th>Score</th><th>Class</th><th>Support</th><th>Conflict</th><th>False Positive</th></tr></thead><tbody>{body}</tbody></table></section>"


def _continuity_table(data: dict) -> str:
    rows = []
    for item in data.get("continuity_rows", [])[:80]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('transition_id'))}</td><td>{_e(item.get('topic_continuity'))}</td><td>{_e(item.get('rhetorical_continuity'))}</td>"
            f"<td>{_e(item.get('emotional_continuity'))}</td><td>{_e(item.get('pacing_continuity'))}</td><td>{_e(item.get('acoustic_continuity'))}</td>"
            f"<td>{_e(item.get('cross_modal_continuity_agreement'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='7'>No continuity rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Transition</th><th>Topic</th><th>Rhetoric</th><th>Emotional</th><th>Pacing</th><th>Acoustic</th><th>Agreement</th></tr></thead><tbody>{body}</tbody></table></section>"


def _transition_table(data: dict) -> str:
    rows = []
    for item in data.get("transitions", [])[:80]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('transition_id'))}</td><td>{_e(item.get('confidence_score'))}</td><td>{_e(item.get('confidence_class'))}</td>"
            f"<td>{_e(item.get('likely_true_transition'))}</td><td>{_e(item.get('likely_false_positive'))}</td>"
            f"<td>{_e(item.get('reasoning_summary'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='6'>No transition rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Transition</th><th>Confidence</th><th>Class</th><th>Likely True</th><th>Likely False</th><th>Reasoning</th></tr></thead><tbody>{body}</tbody></table></section>"


def _modality_table(agreement: dict, disagreement: dict) -> str:
    rows = []
    by_pair = {row.get("modality_pair"): row for row in disagreement.get("modality_pairs", [])}
    for row in agreement.get("modality_pairs", []):
        dis = by_pair.get(row.get("modality_pair"), {})
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('modality_pair'))}</td><td>{_e(row.get('agreement_score'))}</td><td>{_e(dis.get('disagreement_score', row.get('disagreement_score')))}</td><td>{_e(row.get('confidence'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='4'>No modality alignment rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Pair</th><th>Agreement</th><th>Disagreement</th><th>Confidence</th></tr></thead><tbody>{body}</tbody></table></section>"


def _boundary_diagnostics_table(data: dict) -> str:
    rows = []
    for item in data.get("boundaries", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('boundary_id'))}</td><td>{_e(item.get('from_segment_id'))}->{_e(item.get('to_segment_id'))}</td>"
            f"<td>{_e(item.get('consensus_support'))}</td><td>{_e(item.get('contradiction_count'))}</td>"
            f"<td>{_e(item.get('likely_review_boundary'))}</td><td>{_e(item.get('suggested_human_review_action'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='6'>No boundary diagnostic rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Boundary</th><th>Pair</th><th>Support</th><th>Contradictions</th><th>Review</th><th>Action</th></tr></thead><tbody>{body}</tbody></table></section>"


def _discourse_state_table(data: dict) -> str:
    rows = []
    for item in data.get("segment_discourse_states", [])[:100]:
        exiting = item.get("exiting_state") or {}
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('segment_id'))}</td><td>{_e(item.get('discourse_pressure_score'))}</td><td>{_e(item.get('discourse_continuity_score'))}</td>"
            f"<td>{_e(', '.join(exiting.get('active_concepts') or []))}</td>"
            f"<td>{_e(len(exiting.get('unresolved_questions') or []))}</td><td>{_e(len(exiting.get('pending_examples') or []))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='6'>No discourse state rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Segment</th><th>Pressure</th><th>Continuity</th><th>Active Concepts</th><th>Questions</th><th>Pending Examples</th></tr></thead><tbody>{body}</tbody></table></section>"


def _argument_graph_table(data: dict) -> str:
    rows = []
    for item in data.get("argument_chains", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('chain_id'))}</td><td>{_e(item.get('chain_status'))}</td><td>{_e(item.get('chain_strength'))}</td>"
            f"<td>{_e(', '.join(item.get('segment_ids') or []))}</td><td>{_e(len(item.get('node_ids') or []))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='5'>No argument chains available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Chain</th><th>Status</th><th>Strength</th><th>Segments</th><th>Nodes</th></tr></thead><tbody>{body}</tbody></table></section>"


def _narrative_memory_table(data: dict) -> str:
    rows = []
    for item in data.get("persistent_themes", [])[:80]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('term'))}</td><td>{_e(item.get('occurrence_count'))}</td><td>{_e(item.get('span_segments'))}</td>"
            f"<td>{_e(', '.join(item.get('segment_ids') or []))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='4'>No persistent themes available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Theme</th><th>Occurrences</th><th>Span</th><th>Segments</th></tr></thead><tbody>{body}</tbody></table></section>"


def _callback_resolution_table(data: dict) -> str:
    rows = []
    for item in data.get("callback_pairs", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('callback_id'))}</td><td>{_e(item.get('setup_segment_id'))}->{_e(item.get('payoff_segment_id'))}</td>"
            f"<td>{_e(item.get('latency_segments'))}</td><td>{_e(item.get('resolution_confidence'))}</td><td>{_e(item.get('strength_class'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='5'>No callback pairs available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Callback</th><th>Pair</th><th>Latency</th><th>Confidence</th><th>Class</th></tr></thead><tbody>{body}</tbody></table></section>"


def _editorial_ambiguity_table(data: dict) -> str:
    rows = []
    for item in data.get("ambiguity_regions", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('from_segment_id'))}->{_e(item.get('to_segment_id'))}</td><td>{_e(item.get('ambiguity_class'))}</td>"
            f"<td>{_e(item.get('ambiguity_confidence'))}</td><td>{_e('; '.join(item.get('supporting_evidence') or []))}</td>"
            f"<td>{_e('; '.join(item.get('conflicting_evidence') or []))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='5'>No ambiguity regions available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Boundary</th><th>Class</th><th>Confidence</th><th>Supporting Evidence</th><th>Conflicting Evidence</th></tr></thead><tbody>{body}</tbody></table></section>"


def _shot_boundary_table(data: dict) -> str:
    rows = []
    for item in data.get("detected_boundaries", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('boundary_id'))}</td><td>{_e(item.get('timestamp_sec'))}</td>"
            f"<td>{_e(item.get('boundary_confidence'))}</td><td>{_e(item.get('visual_change_score'))}</td>"
            f"<td>{_e('; '.join(item.get('neighboring_frame_paths') or []))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='5'>No shot boundaries available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Boundary</th><th>Time</th><th>Confidence</th><th>Change</th><th>Frames</th></tr></thead><tbody>{body}</tbody></table></section>"


def _visual_continuity_table(data: dict) -> str:
    rows = []
    for item in data.get("visual_reset_candidates", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('reset_candidate_id'))}</td><td>{_e(item.get('timestamp_sec'))}</td>"
            f"<td>{_e(item.get('visual_reset_strength'))}</td><td>{_e(item.get('review_action'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='4'>No visual reset candidates available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Candidate</th><th>Time</th><th>Strength</th><th>Review Action</th></tr></thead><tbody>{body}</tbody></table></section>"


def _composition_table(data: dict) -> str:
    rows = []
    for item in data.get("segment_summaries", [])[:100]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('segment_id'))}</td><td>{_e(item.get('sample_count'))}</td>"
            f"<td>{_e(item.get('mean_complexity'))}</td><td>{_e(item.get('visual_energy'))}</td>"
            f"<td>{_e(item.get('visual_stillness'))}</td><td>{_e(item.get('abruptness'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='6'>No composition segment summaries available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Segment</th><th>Samples</th><th>Complexity</th><th>Energy</th><th>Stillness</th><th>Abruptness</th></tr></thead><tbody>{body}</tbody></table></section>"


def _visual_alignment_table(data: dict) -> str:
    rows = []
    for item in data.get("boundaries", [])[:120]:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('from_segment_id'))}->{_e(item.get('to_segment_id'))}</td>"
            f"<td>{_e(item.get('visual_support'))}</td><td>{_e(item.get('transcript_support'))}</td>"
            f"<td>{_e(item.get('rhetorical_support'))}</td><td>{_e(item.get('discourse_support'))}</td>"
            f"<td>{_e(item.get('acoustic_support'))}</td><td>{_e(item.get('visual_contradiction'))}</td>"
            f"<td>{_e(item.get('boundary_evidence_type'))}</td><td>{_e(item.get('suggested_review_action'))}</td>"
            "</tr>"
        )
    body = "\n".join(rows) or "<tr><td colspan='9'>No visual alignment rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Boundary</th><th>Visual</th><th>Transcript</th><th>Rhetorical</th><th>Discourse</th><th>Acoustic</th><th>Contradiction</th><th>Type</th><th>Action</th></tr></thead><tbody>{body}</tbody></table></section>"


def _frame_rows(samples: list[dict], segments: list[dict], transcript_segments: list[dict]) -> str:
    rows = []
    for sample in samples:
        timestamp = float(sample.get("timestamp") or 0)
        segment_id = next((segment.get("segment_id") for segment in segments if float(segment.get("start_sec") or 0) <= timestamp <= float(segment.get("end_sec") or 0)), "")
        snippet = next((segment.get("text", "") for segment in transcript_segments if float(segment.get("start") or 0) <= timestamp <= float(segment.get("end") or 0)), "")
        rows.append(
            "<tr>"
            f"<td>{_e(sample.get('sample_id'))}</td>"
            f"<td>{_e(timestamp)}</td>"
            f"<td>{_e(segment_id)}</td>"
            f"<td>{_e(sample.get('status'))}</td>"
            f"<td>{_e(sample.get('reason'))}</td>"
            f"<td>{_e(snippet[:160])}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='6'>No frame samples available.</td></tr>"


def _write_interactive_outputs(bundle) -> dict:
    try:
        import plotly.graph_objects as go
        from plotly.offline import plot
    except Exception as exc:  # pragma: no cover - optional dependency
        return {"status": "skipped", "reason": f"Plotly unavailable: {exc}", "files": []}

    out_dir = bundle.output_dir / "interactive"
    out_dir.mkdir(exist_ok=True)
    written: list[str] = []

    def write_fig(filename: str, fig) -> None:
        plot(fig, filename=str(out_dir / filename), auto_open=False, include_plotlyjs=True)
        written.append(filename)

    emotional = bundle.emotional_arc.get("segments") or []
    if emotional:
        x = [(float(row.get("start_sec") or 0) + float(row.get("end_sec") or 0)) / 2 for row in emotional]
        fig = go.Figure()
        for key in ["energy", "valence", "certainty", "intensity"]:
            fig.add_trace(go.Scatter(x=x, y=[row.get(key) for row in emotional], mode="lines+markers", name=key))
        fig.update_layout(title="Emotional Arc Interactive", xaxis_title="Seconds", yaxis_title="Score")
        write_fig("emotional_arc_interactive.html", fig)

    rates = bundle.audio_features.get("segment_speech_rate") or []
    if rates:
        fig = go.Figure(data=[go.Scatter(x=[row.get("start_sec") for row in rates], y=[row.get("words_per_minute") for row in rates], mode="lines+markers", name="WPM")])
        fig.update_layout(title="Pacing Interactive", xaxis_title="Seconds", yaxis_title="Words per minute")
        write_fig("pacing_interactive.html", fig)

    acoustic_rows = (getattr(bundle, "acoustic_features", None) or {}).get("rms_energy_over_time") or []
    if acoustic_rows:
        step = max(1, len(acoustic_rows) // 1200)
        sampled = acoustic_rows[::step]
        fig = go.Figure(data=[go.Scatter(x=[row.get("time_sec") for row in sampled], y=[row.get("rms") for row in sampled], mode="lines", name="RMS")])
        fig.update_layout(title="Acoustic Energy Interactive", xaxis_title="Seconds", yaxis_title="RMS")
        write_fig("acoustic_energy_interactive.html", fig)

    topic_rows = (getattr(bundle, "topic_analysis", None) or {}).get("per_segment_keywords") or []
    if topic_rows:
        fig = go.Figure(data=[go.Bar(x=[row.get("segment_id") for row in topic_rows], y=[len(row.get("keywords") or []) for row in topic_rows], text=[row.get("topic_label") for row in topic_rows])])
        fig.update_layout(title="Topic Timeline Interactive", xaxis_title="Segment", yaxis_title="Keyword count")
        write_fig("topic_timeline_interactive.html", fig)

    segments = bundle.scene_segments.get("segments") or []
    if segments:
        fig = go.Figure(data=[go.Bar(x=[row.get("duration_sec") for row in segments], y=[row.get("segment_id") for row in segments], orientation="h", text=[row.get("summary") for row in segments])])
        fig.update_layout(title="Segment Timeline Interactive", xaxis_title="Duration seconds", yaxis_title="Segment")
        write_fig("segment_timeline_interactive.html", fig)

    profile_rows = (bundle.persona_profile.get("top_categories") or [])[:8]
    if profile_rows:
        fig = go.Figure(data=[go.Bar(x=[row.get("label") for row in profile_rows], y=[row.get("weight") for row in profile_rows])])
        fig.update_layout(title="Persona Style Interactive", xaxis_title="Category", yaxis_title="Weight")
        write_fig("persona_style_interactive.html", fig)

    return {"status": "complete" if written else "skipped", "reason": None if written else "No source rows were available for interactive charts.", "files": written}


def _matching_markers(text: str) -> list[str]:
    lowered = (text or "").lower()
    return [label for label, markers in MARKERS.items() if any(marker in lowered for marker in markers)]


def _tone_for(start, rows) -> str:
    try:
        current = float(start or 0)
    except Exception:
        return "neutral"
    for row_start, row_end, tone, _intensity in rows:
        if float(row_start or 0) <= current <= float(row_end or 0):
            return tone or "neutral"
    return "neutral"


def _wpm_for(segment: dict) -> float:
    text = segment.get("text", "")
    duration = max(float(segment.get("end", 0) or 0) - float(segment.get("start", 0) or 0), 0.001)
    return round(len(text.split()) / (duration / 60.0), 2) if text else 0.0


def _arc_table(rows: list[dict]) -> str:
    body = "".join(
        f"<tr><td>{_e(row.get('start_sec'))}-{_e(row.get('end_sec'))}</td><td>{_e(row.get('dominant_tone'))}</td><td>{_e(row.get('energy'))}</td><td>{_e(row.get('valence'))}</td><td>{_e(row.get('intensity'))}</td><td>{_e('; '.join(row.get('evidence') or []))}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='6'>No emotional arc rows available.</td></tr>"
    return f"<section class='panel'><table><thead><tr><th>Time</th><th>Tone</th><th>Energy</th><th>Valence</th><th>Intensity</th><th>Evidence</th></tr></thead><tbody>{body}</tbody></table></section>"


def _json_block(data: dict) -> str:
    return f"<section class='panel'><h2>Statistics</h2><pre>{_e(json.dumps(data, indent=2, ensure_ascii=False))}</pre></section>"


def _keywords(report_data: dict) -> str:
    items = report_data.get("transcript_statistics", {}).get("top_keywords", [])[:30]
    return "<section class='panel'><h2>Keywords</h2><div class='chips'>" + "".join(f"<span>{_e(item['term'])} <b>{_e(item['count'])}</b></span>" for item in items) + "</div></section>"


def _markdownish(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("# "):
            lines.append(f"<h2>{_e(line[2:])}</h2>")
        elif line.startswith("## "):
            lines.append(f"<h3>{_e(line[3:])}</h3>")
        elif line.startswith("- "):
            lines.append(f"<p class='bullet'>{_e(line[2:])}</p>")
        elif line.strip():
            lines.append(f"<p>{_e(line)}</p>")
    return "\n".join(lines)
