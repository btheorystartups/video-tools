# Visualization and Reporting Layer

The visualization layer is a local-first artifact writer. It adds static HTML,
PNG graphs, JSON statistics, and Markdown reports to each analysis directory.
It does not start a server, use cloud APIs, add a database, or call an LLM.

## Install

```powershell
py -3 -m pip install matplotlib plotly pandas numpy scipy networkx pyvis jinja2 seaborn scikit-learn wordcloud pillow librosa textstat
```

Equivalent file-based install:

```powershell
py -3 -m pip install -r .\tools\video-insight-bundler\requirements-visualization.txt
```

## Required for Current Visualization Output

- `matplotlib`: PNG graph generation.

## Optional Enhancements Used When Available

- `networkx`: rhetorical marker network layout.
- `wordcloud`: transcript word cloud.
- `textstat`: transcript readability statistics.
- `jinja2`: reserved for external templates as the layer grows.
- `pillow`: image fallback support.
- `plotly`: optional self-contained interactive HTML charts.
- `pandas`: table-oriented statistics.
- `numpy`: numeric support.
- `scipy`: signal/statistical analysis.
- `pyvis`: future interactive network artifacts.
- `seaborn`: future statistical graph styling.
- `scikit-learn`: local TF-IDF topic analysis and deterministic clustering.
- `librosa`: local acoustic energy, silence, spectral, and rhythm proxy analysis.

## Generated Structure

```text
<video>_analysis/
  visualizations/
    dashboard.html
    transcript_explorer.html
    emotional_arc.html
    pacing_analysis.html
    persona_analysis.html
    rhetorical_flow.html
    segment_timeline.html
    transcript_density.html
    recommendations_report.html
    acoustic_analysis.html
    topic_analysis.html
    rhetorical_deep_dive.html
    segment_quality.html
    frame_contact_sheet.html
    revision_graph.html
    revision_comparison.html
    release_readiness.html
    mutation_safety.html
    editorial_evolution.html
    evidence_consensus.html
    continuity_analysis.html
    segmentation_confidence.html
    modality_alignment.html
    topic_continuity.html
    rhetorical_coherence.html
    boundary_diagnostics.html
    discourse_state.html
    argument_graph.html
    narrative_memory.html
    callback_resolution.html
    editorial_ambiguity.html
    visual_structure.html
    shot_boundaries.html
    visual_continuity.html
    composition_features.html
    visual_boundary_alignment.html
  graphs/
    emotional_arc.png
    pacing_curve.png
    transcript_density.png
    persona_radar.png
    rhetorical_heatmap.png
    segment_timeline.png
    speaking_rate_distribution.png
    pause_distribution.png
    rhetorical_markers_network.png
    keyword_clusters.png
    wordcloud.png
    acoustic_energy_curve.png
    segment_energy_bars.png
    silence_ratio.png
    acoustic_variability.png
    topic_timeline.png
    topic_shift_heatmap.png
    keyword_importance.png
    concept_repetition.png
    rhetorical_mode_timeline.png
    question_density.png
    claim_example_balance.png
    abstract_vs_concrete.png
    audience_address_curve.png
    segment_boundary_confidence.png
    frame_contact_sheet.png
    revision_score_evolution.png
    branch_comparison.png
    release_readiness_radar.png
    constraint_pressure.png
    mutation_safety_matrix.png
    editorial_evolution.png
    modality_agreement_heatmap.png
    modality_disagreement_heatmap.png
    transition_confidence_curve.png
    evidence_strength_distribution.png
    continuity_alignment.png
    false_positive_boundaries.png
    segmentation_confidence.png
    topic_continuity_curve.png
    topic_bridge_map.png
    rhetorical_coherence_timeline.png
    claim_evidence_balance.png
    boundary_diagnostic_matrix.png
    discourse_flow_graph.png
    argument_chain_graph.png
    callback_resolution_map.png
    narrative_memory_timeline.png
    discourse_pressure_curve.png
    ambiguity_distribution.png
    unresolved_argument_map.png
    shot_boundary_curve.png
    visual_change_intensity.png
    visual_continuity_timeline.png
    composition_complexity_curve.png
    frame_difference_heatmap.png
    visual_boundary_alignment.png
    shot_contact_sheet.png
  interactive/
    emotional_arc_interactive.html
    pacing_interactive.html
    acoustic_energy_interactive.html
    topic_timeline_interactive.html
    segment_timeline_interactive.html
    persona_style_interactive.html
  reports/
    quality_report.md
    quality_report.json
    transcript_statistics.json
    rhetorical_statistics.json
    segment_statistics.json
    pacing_statistics.json
    acoustic_statistics.json
    topic_statistics.json
    rhetorical_deep_dive.json
    segment_boundary_report.json
    revision_graph_summary.md
    revision_graph_summary.json
    release_readiness_summary.md
    branch_comparison_summary.md
    mutation_safety_summary.md
    evidence_consensus_report.md
    evidence_consensus_report.json
    continuity_report.md
    continuity_report.json
    segmentation_confidence_report.md
    segmentation_confidence_report.json
    topic_continuity_report.md
    rhetorical_coherence_report.md
    boundary_diagnostics_report.md
    discourse_state_report.md
    argument_graph_report.md
    narrative_memory_report.md
    callback_resolution_report.md
    editorial_ambiguity_report.md
    visual_structure_report.md
    shot_boundary_report.md
    visual_continuity_report.md
    composition_features_report.md
    visual_boundary_alignment_report.md
  static_assets/
    report.css
    report.js
```

All HTML paths are relative. The dashboard can be opened directly from disk.

The dashboard includes Consensus Summary, Topic Continuity, Rhetorical Coherence, Boundary Diagnostics, Discourse State, Argument Graph, Narrative Memory, Callback Resolution, Editorial Ambiguity, Visual Structure, Continuity Decomposition, and Revision Intelligence sections. Consensus pages show evidence strength, modality agreement/disagreement, transition confidence, false-positive boundary flags, and continuity alignment. Continuity and discourse pages show topic bridge support, rhetorical gap evidence, argument-chain state, setup/payoff links, callback maps, ambiguity regions, and boundary review actions. Visual pages show shot-boundary curves, visual change intensity, continuity timelines, composition complexity, frame-difference heatmaps, shot contact sheets, and visual-boundary alignment. Revision pages show proposal-only branch comparisons, release readiness, mutation safety, constraint pressure, and editorial evolution. They read local JSON artifacts and do not require a server.

Interactive Plotly files are generated only when `plotly` is installed. They are written as self-contained HTML files with embedded Plotly JavaScript, so they do not require a server.

All acoustic, rhetorical, persona, emotional, and topic outputs are heuristic evidence summaries for human review. They are not psychological, clinical, identity, or intent claims.

Revision graph outputs are planning and simulation artifacts. They do not apply edits, mutate media, change Resolve timelines, or guarantee publication readiness. They are deterministic decision-support artifacts for human review.

Consensus outputs are deterministic evidence-fusion heuristics intended to improve explainability and editorial review. They are not semantic truth guarantees or autonomous editorial decisions.

Topic continuity and rhetorical coherence are deterministic local heuristics for editorial review. They are not semantic truth guarantees.

Discourse, argument, callback, and ambiguity outputs are deterministic editorial-review heuristics intended to improve explainability and human review. They are not semantic truth guarantees, intent detection systems, or autonomous editorial decisions.

Visual structure outputs are deterministic pixel/color/edge-level evidence summaries for editorial review. They are not object recognition, identity detection, emotion recognition, or cinematic intent claims.
# Integrity Dashboards

The static visualization set now includes Artifact Integrity, Graph Consistency, Reference Validation, Lineage Validation, Migration Registry, and Semantic Readiness pages. All pages use relative links and degrade to JSON summaries plus placeholder graphs when optional plotting dependencies are unavailable.
